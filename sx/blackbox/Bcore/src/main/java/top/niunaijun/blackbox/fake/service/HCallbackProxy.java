package top.niunaijun.blackbox.fake.service;

import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.content.pm.ServiceInfo;
import android.os.Handler;
import android.os.IBinder;
import android.os.Message;

import androidx.annotation.NonNull;

import java.lang.reflect.Proxy;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

import black.android.app.ActivityThreadActivityClientRecordContext;
import black.android.app.BRActivityClient;
import black.android.app.BRActivityClientActivityClientControllerSingleton;
import black.android.app.BRActivityManagerNative;
import black.android.app.BRActivityThread;
import black.android.app.BRActivityThreadActivityClientRecord;
import black.android.app.BRActivityThreadCreateServiceData;
import black.android.app.BRActivityThreadH;
import black.android.app.BRIActivityManager;
import black.android.app.servertransaction.BRClientTransaction;
import black.android.app.servertransaction.BRLaunchActivityItem;
import black.android.app.servertransaction.LaunchActivityItemContext;
import black.android.os.BRHandler;
import top.niunaijun.blackbox.BlackBoxCore;
import top.niunaijun.blackbox.app.BActivityThread;
import top.niunaijun.blackbox.fake.hook.IInjectHook;
import top.niunaijun.blackbox.proxy.ProxyManifest;
import top.niunaijun.blackbox.proxy.record.ProxyActivityRecord;
import top.niunaijun.blackbox.utils.Slog;
import top.niunaijun.blackbox.utils.compat.BuildCompat;


/**
 * Created by Milk on 3/31/21.
 * * ∧＿∧
 * (`･ω･∥
 * 丶　つ０
 * しーＪ
 * 此处无Bug
 */
public class HCallbackProxy implements IInjectHook, Handler.Callback {
    public static final String TAG = "HCallbackStub";
    private Handler.Callback mOtherCallback;
    private AtomicBoolean mBeing = new AtomicBoolean(false);

    private Handler.Callback getHCallback() {
        return BRHandler.get(getH()).mCallback();
    }

    private Handler getH() {
        Object currentActivityThread = BlackBoxCore.mainThread();
        return BRActivityThread.get(currentActivityThread).mH();
    }

    @Override
    public void injectHook() {
        mOtherCallback = getHCallback();
        if (mOtherCallback != null && (mOtherCallback == this || mOtherCallback.getClass().getName().equals(this.getClass().getName()))) {
            mOtherCallback = null;
        }
        BRHandler.get(getH())._set_mCallback(this);
    }

    @Override
    public boolean isBadEnv() {
        Handler.Callback hCallback = getHCallback();
        return hCallback != null && hCallback != this;
    }

    @Override
    public boolean handleMessage(@NonNull Message msg) {
        if (!mBeing.getAndSet(true)) {
            try {
                if (BuildCompat.isPie()) {
                    Integer executeTransaction = BRActivityThreadH.get().EXECUTE_TRANSACTION();
                    android.util.Log.e(TAG, "HCallbackProxy msg.what=" + msg.what + ", executeTransaction=" + executeTransaction);
                    if (executeTransaction != null && msg.what == executeTransaction) {
                        if (handleLaunchActivity(msg.obj)) {
                            getH().sendMessageDelayed(Message.obtain(msg), 10);
                            return true;
                        }
                    }
                } else {
                    Integer launchActivity = BRActivityThreadH.get().LAUNCH_ACTIVITY();
                    if (launchActivity != null && msg.what == launchActivity) {
                        if (handleLaunchActivity(msg.obj)) {
                            getH().sendMessageDelayed(Message.obtain(msg), 10);
                            return true;
                        }
                    }
                }
                Integer createService = BRActivityThreadH.get().CREATE_SERVICE();
                if (createService != null && msg.what == createService) {
                    return handleCreateService(msg.obj);
                }
                if (mOtherCallback != null) {
                    return mOtherCallback.handleMessage(msg);
                }
                return false;
            } finally {
                mBeing.set(false);
            }
        }
        return false;
    }

    private Object getLaunchActivityItem(Object clientTransaction) {
        try {
            List<Object> mActivityCallbacks = BRClientTransaction.get(clientTransaction).mActivityCallbacks();
            if (mActivityCallbacks == null || mActivityCallbacks.isEmpty()) {
                return null;
            }

            for (Object obj : mActivityCallbacks) {
                if (obj == null) {
                    continue;
                }
                if ("android.app.servertransaction.LaunchActivityItem".equals(obj.getClass().getName())) {
                    return obj;
                }
            }
        } catch (Throwable t) {
            android.util.Log.e(TAG, "getLaunchActivityItem failed", t);
        }
        return null;
    }

    private boolean handleLaunchActivity(Object client) {
        Object r;
        if (BuildCompat.isPie()) {
            // ClientTransaction
            r = getLaunchActivityItem(client);
        } else {
            // ActivityClientRecord
            r = client;
        }
        if (r == null)
            return false;

        Intent intent = null;
        IBinder token = null;
        if (BuildCompat.isPie()) {
            try {
                java.lang.reflect.Field fIntent = r.getClass().getDeclaredField("mIntent");
                fIntent.setAccessible(true);
                intent = (Intent) fIntent.get(r);
            } catch (Throwable t) {
                android.util.Log.e(TAG, "Failed to get mIntent from LaunchActivityItem: " + t.getMessage());
            }
            try {
                java.lang.reflect.Field fToken = client.getClass().getDeclaredField("mActivityToken");
                fToken.setAccessible(true);
                token = (IBinder) fToken.get(client);
            } catch (Throwable t) {
                android.util.Log.e(TAG, "Failed to get mActivityToken from ClientTransaction: " + t.getMessage());
            }
        } else {
            ActivityThreadActivityClientRecordContext clientRecordContext = BRActivityThreadActivityClientRecord.get(r);
            intent = clientRecordContext.intent();
            token = clientRecordContext.token();
        }

        if (intent == null) {
            android.util.Log.e(TAG, "handleLaunchActivity: intent is NULL!");
            return false;
        }

        ProxyActivityRecord stubRecord = ProxyActivityRecord.create(intent);
        ActivityInfo activityInfo = stubRecord.mActivityInfo;
        if (activityInfo != null) {
            if (BActivityThread.getAppConfig() == null) {
                BlackBoxCore.getBActivityManager().restartProcess(activityInfo.packageName, activityInfo.processName, stubRecord.mUserId);

                Intent launchIntentForPackage = BlackBoxCore.getBPackageManager().getLaunchIntentForPackage(activityInfo.packageName, stubRecord.mUserId);
                intent.setExtrasClassLoader(this.getClass().getClassLoader());
                ProxyActivityRecord.saveStub(intent, launchIntentForPackage, stubRecord.mActivityInfo, stubRecord.mActivityRecord, stubRecord.mUserId);
                if (BuildCompat.isPie()) {
                    try {
                        java.lang.reflect.Field fIntent = r.getClass().getDeclaredField("mIntent");
                        fIntent.setAccessible(true);
                        fIntent.set(r, intent);
                        java.lang.reflect.Field fInfo = r.getClass().getDeclaredField("mInfo");
                        fInfo.setAccessible(true);
                        fInfo.set(r, activityInfo);
                        android.util.Log.i(TAG, "Direct reflection init LaunchActivityItem -> " + activityInfo.name);
                    } catch (Throwable t) {
                        android.util.Log.e(TAG, "Direct reflection init LaunchActivityItem failed", t);
                    }
                } else {
                    ActivityThreadActivityClientRecordContext clientRecordContext = BRActivityThreadActivityClientRecord.get(r);
                    clientRecordContext._set_intent(intent);
                    clientRecordContext._set_activityInfo(activityInfo);
                }
                return true;
            }
            // bind
            if (!BActivityThread.currentActivityThread().isInit()) {
                BActivityThread.currentActivityThread().bindApplication(activityInfo.packageName,
                        activityInfo.processName);
            }

            int taskId = BRIActivityManager.get(BRActivityManagerNative.get().getDefault()).getTaskForActivity(token, false);
            BlackBoxCore.getBActivityManager().onActivityCreated(taskId, token, stubRecord.mActivityRecord);

            if (BuildCompat.isPie()) {
                // Always rewrite LaunchActivityItem via direct reflection on Android 9–14.
                try {
                    java.lang.reflect.Field fIntent = r.getClass().getDeclaredField("mIntent");
                    fIntent.setAccessible(true);
                    fIntent.set(r, stubRecord.mTarget);
                    java.lang.reflect.Field fInfo = r.getClass().getDeclaredField("mInfo");
                    fInfo.setAccessible(true);
                    fInfo.set(r, activityInfo);
                    android.util.Log.e(TAG, "Direct reflection rewrote LaunchActivityItem -> " + activityInfo.name);
                } catch (Throwable t) {
                    android.util.Log.e(TAG, "Direct reflection LaunchActivityItem rewrite failed", t);
                }

                // Android 12+ (Android S): ActivityThread reads ActivityClientRecord from mLaunchingActivities / mActivities
                Object mainThread = BlackBoxCore.mainThread();
                if (mainThread != null && token != null) {
                    try {
                        java.lang.reflect.Method getLaunchingActivityMethod = mainThread.getClass().getDeclaredMethod("getLaunchingActivity", IBinder.class);
                        getLaunchingActivityMethod.setAccessible(true);
                        Object record = getLaunchingActivityMethod.invoke(mainThread, token);
                        if (record != null) {
                            java.lang.reflect.Field fIntent = record.getClass().getDeclaredField("intent");
                            fIntent.setAccessible(true);
                            fIntent.set(record, stubRecord.mTarget);
                            java.lang.reflect.Field fInfo = record.getClass().getDeclaredField("activityInfo");
                            fInfo.setAccessible(true);
                            fInfo.set(record, activityInfo);
                            java.lang.reflect.Field fPackageInfo = record.getClass().getDeclaredField("packageInfo");
                            fPackageInfo.setAccessible(true);
                            fPackageInfo.set(record, BActivityThread.currentActivityThread().getPackageInfo());
                            android.util.Log.e(TAG, "Direct reflection rewrote getLaunchingActivity -> " + activityInfo.name);
                        }
                    } catch (Throwable t) {
                        android.util.Log.w(TAG, "Direct reflection rewrite getLaunchingActivity failed: " + t.getMessage());
                    }
                    try {
                        java.lang.reflect.Field fActivities = mainThread.getClass().getDeclaredField("mActivities");
                        fActivities.setAccessible(true);
                        java.util.Map mActivities = (java.util.Map) fActivities.get(mainThread);
                        if (mActivities != null) {
                            Object record = mActivities.get(token);
                            if (record != null) {
                                java.lang.reflect.Field fIntent = record.getClass().getDeclaredField("intent");
                                fIntent.setAccessible(true);
                                fIntent.set(record, stubRecord.mTarget);
                                java.lang.reflect.Field fInfo = record.getClass().getDeclaredField("activityInfo");
                                fInfo.setAccessible(true);
                                fInfo.set(record, activityInfo);
                                java.lang.reflect.Field fPackageInfo = record.getClass().getDeclaredField("packageInfo");
                                fPackageInfo.setAccessible(true);
                                fPackageInfo.set(record, BActivityThread.currentActivityThread().getPackageInfo());
                                android.util.Log.e(TAG, "Direct reflection rewrote mActivities -> " + activityInfo.name);
                            }
                        }
                    } catch (Throwable t) {
                        android.util.Log.w(TAG, "Direct reflection rewrite mActivities failed: " + t.getMessage());
                    }
                }
            } else {
                ActivityThreadActivityClientRecordContext clientRecordContext = BRActivityThreadActivityClientRecord.get(r);
                clientRecordContext._set_intent(stubRecord.mTarget);
                clientRecordContext._set_activityInfo(activityInfo);
            }
        }
        return false;
    }

    private boolean handleCreateService(Object data) {
        if (BActivityThread.getAppConfig() != null) {
            String appPackageName = BActivityThread.getAppPackageName();
            assert appPackageName != null;

            ServiceInfo serviceInfo = BRActivityThreadCreateServiceData.get(data).info();
            if (!serviceInfo.name.equals(ProxyManifest.getProxyService(BActivityThread.getAppPid()))
                    && !serviceInfo.name.equals(ProxyManifest.getProxyJobService(BActivityThread.getAppPid()))) {
                Slog.d(TAG, "handleCreateService: " + data);
                Intent intent = new Intent();
                intent.setComponent(new ComponentName(appPackageName, serviceInfo.name));
                BlackBoxCore.getBActivityManager().startService(intent, null, false, BActivityThread.getUserId());
                return true;
            }
        }
        return false;
    }

    private void checkActivityClient() {
        try {
            Object activityClientController = BRActivityClient.get().getActivityClientController();
            if (!(activityClientController instanceof Proxy)) {
                IActivityClientProxy iActivityClientProxy = new IActivityClientProxy(activityClientController);
                iActivityClientProxy.onlyProxy(true);
                iActivityClientProxy.injectHook();
                Object instance = BRActivityClient.get().getInstance();
                Object o = BRActivityClient.get(instance).INTERFACE_SINGLETON();
                BRActivityClientActivityClientControllerSingleton.get(o)._set_mKnownInstance(iActivityClientProxy.getProxyInvocation());
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }
}
