package top.niunaijun.blackbox.fake.service;

import android.app.ActivityManager;
import android.os.IBinder;

import java.lang.reflect.Method;

import black.android.app.BRActivityClient;
import black.android.util.BRSingleton;
import top.niunaijun.blackbox.fake.frameworks.BActivityManager;
import top.niunaijun.blackbox.fake.hook.ClassInvocationStub;
import top.niunaijun.blackbox.fake.hook.MethodHook;
import top.niunaijun.blackbox.fake.hook.ProxyMethod;
import top.niunaijun.blackbox.utils.compat.TaskDescriptionCompat;

/**
 * Created by BlackBox on 2022/2/22.
 */
public class IActivityClientProxy extends ClassInvocationStub {
    public static final String TAG = "IActivityClientProxy";
    private final Object who;

    public IActivityClientProxy(Object who) {
        this.who = who;
    }

    @Override
    protected Object getWho() {
        if (who != null) {
            return who;
        }
        Object instance = BRActivityClient.get().getInstance();
        Object singleton = BRActivityClient.get(instance).INTERFACE_SINGLETON();
        return BRSingleton.get(singleton).get();
    }

    @Override
    protected void inject(Object baseInvocation, Object proxyInvocation) {
        Object instance = BRActivityClient.get().getInstance();
        Object singleton = BRActivityClient.get(instance).INTERFACE_SINGLETON();
        BRSingleton.get(singleton)._set_mInstance(proxyInvocation);
    }

    @Override
    public boolean isBadEnv() {
        return false;
    }

    @Override
    public Object getProxyInvocation() {
        return super.getProxyInvocation();
    }

    @Override
    public void onlyProxy(boolean o) {
        super.onlyProxy(o);
    }

    @ProxyMethod("finishActivity")
    public static class FinishActivity extends MethodHook {
        @Override
        protected Object hook(Object who, Method method, Object[] args) throws Throwable {
            IBinder token = (IBinder) args[0];
            // ProxyActivity trampoline finish must not remove the guest virtual activity that
            // was registered against the same shell token.
            if (!isProxyShellFinish(token)) {
                BActivityManager.get().onFinishActivity(token);
            }
            return method.invoke(who, args);
        }

        private static boolean isProxyShellFinish(IBinder token) {
            try {
                android.app.Activity activity =
                        top.niunaijun.blackbox.app.BActivityThread.getActivityByToken(token);
                if (activity == null) {
                    return false;
                }
                if (activity instanceof top.niunaijun.blackbox.proxy.ProxyActivity
                        || activity instanceof top.niunaijun.blackbox.proxy.TransparentProxyActivity) {
                    return true;
                }
                android.content.Intent intent = activity.getIntent();
                return intent != null && intent.getBooleanExtra("_B_|_proxy_shell_finish_", false);
            } catch (Throwable t) {
                return false;
            }
        }
    }

    @ProxyMethod("activityResumed")
    public static class ActivityResumed extends MethodHook {
        @Override
        protected Object hook(Object who, Method method, Object[] args) throws Throwable {
            IBinder token = (IBinder) args[0];
            BActivityManager.get().onActivityResumed(token);
            return method.invoke(who, args);
        }
    }

    @ProxyMethod("activityDestroyed")
    public static class ActivityDestroyed extends MethodHook {
        @Override
        protected Object hook(Object who, Method method, Object[] args) throws Throwable {
            IBinder token = (IBinder) args[0];
            BActivityManager.get().onActivityDestroyed(token);
            return method.invoke(who, args);
        }
    }

    // for >= Android 12
    @ProxyMethod("setTaskDescription")
    public static class SetTaskDescription extends MethodHook {
        @Override
        protected Object hook(Object who, Method method, Object[] args) throws Throwable {
            ActivityManager.TaskDescription td = (ActivityManager.TaskDescription) args[1];
            args[1] = TaskDescriptionCompat.fix(td);
            return method.invoke(who, args);
        }
    }

    /**
     * Activity.isTaskRoot() on API 31+ is:
     *   ActivityClient.getTaskForActivity(token, onlyRoot=true) >= 0
     *
     * BlackBox launches guests under a host ProxyActivity shell, so the system task root is
     * ProxyActivity — guests (HyperOS DeskClock) see isTaskRoot=false and call finish()+MAIN.
     * When onlyRoot=true, force onlyRoot=false and return the real task id so isTaskRoot() is true.
     */
    @ProxyMethod("getTaskForActivity")
    public static class GetTaskForActivity extends MethodHook {
        @Override
        protected Object hook(Object who, Method method, Object[] args) throws Throwable {
            if (args != null && args.length >= 2 && Boolean.TRUE.equals(args[1])) {
                Object[] copy = args.clone();
                copy[1] = false;
                Object result = method.invoke(who, copy);
                if (result instanceof Integer && ((Integer) result) >= 0) {
                    return result;
                }
                // Still claim root so guest launchers do not finish immediately.
                return 1;
            }
            return method.invoke(who, args);
        }
    }

    /**
     * Some OEM/framework paths use isTopOfTask when deciding task ownership.
     * Returning true is safe for single-activity guest launchers under Proxy shell.
     */
    @ProxyMethod("isTopOfTask")
    public static class IsTopOfTask extends MethodHook {
        @Override
        protected Object hook(Object who, Method method, Object[] args) throws Throwable {
            return true;
        }
    }
}
