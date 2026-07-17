package com.loc.va.test;

import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.icu.lang.UCharacter;
import android.os.Bundle;
import android.os.Process;
import android.util.Log;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;
import b.k0;
import com.lody.virtual.client.core.j;
import com.lody.virtual.client.ipc.VActivityManager;
import com.lody.virtual.os.VUserHandle;
import com.stub.StubApp;
import java.security.SecureRandom;
import java.util.Random;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class BroadcastTestActivity extends Activity {
    

    /* renamed from: b, reason: collision with root package name */
    EditText f22703b;

    /* renamed from: d, reason: collision with root package name */
    TextView f22705d;

    /* renamed from: e, reason: collision with root package name */
    String f22706e;

    /* renamed from: a, reason: collision with root package name */
    int f22702a = Process.myPid();

    /* renamed from: c, reason: collision with root package name */
    Random f22704c = new SecureRandom();

    /* renamed from: f, reason: collision with root package name */
    String f22707f = "VA_BroadcastTest_io.busniess.va";

    /* renamed from: g, reason: collision with root package name */
    BroadcastReceiver f22708g = new e();

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class a implements View.OnClickListener {
        

        

        a() {
        }

        @Override // android.view.View.OnClickListener
        public void onClick(View view) {
            Intent intent = new Intent(BroadcastTestActivity.this.f22706e);
            intent.putExtra("pid", BroadcastTestActivity.this.f22702a);
            intent.putExtra("msg", BroadcastTestActivity.this.f22703b.getText());
            intent.putExtra("pkg", BroadcastTestActivity.this.getPackageName());
            BroadcastTestActivity.this.f22705d.setText("发送广播: " + intent.getAction());
            BroadcastTestActivity.this.sendBroadcast(intent);
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* loaded from: D:\github\xh\blackdex_out\classes10.dex */
    class b implements View.OnClickListener {
        

        

        b() {
        }

        @Override // android.view.View.OnClickListener
        public void onClick(View view) {
            BroadcastTestActivity.this.f22705d.setText("发送广播失败\n无法获取外部app的pid信息");
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class c implements View.OnClickListener {
        

        

        c() {
        }

        @Override // android.view.View.OnClickListener
        public void onClick(View view) {
            String obj = BroadcastTestActivity.this.f22703b.getText().toString();
            int j5 = j.h().j(obj, 0, obj);
            if (j5 <= 0) {
                BroadcastTestActivity.this.f22705d.setText("VApp1 没有启动, 无法发送广播!!!");
            } else {
                BroadcastTestActivity.this.c(j5);
            }
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* loaded from: D:\github\xh\blackdex_out\classes10.dex */
    class d implements View.OnClickListener {
        

        

        d() {
        }

        @Override // android.view.View.OnClickListener
        public void onClick(View view) {
            String obj = BroadcastTestActivity.this.f22703b.getText().toString();
            int j5 = j.h().j(obj, 1, obj);
            if (j5 <= 0) {
                BroadcastTestActivity.this.f22705d.setText("VApp2 没有启动, 无法发送广播!!!");
            } else {
                BroadcastTestActivity.this.c(j5);
            }
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class e extends BroadcastReceiver {
        

        

        e() {
        }

        @Override // android.content.BroadcastReceiver
        public void onReceive(Context context, Intent intent) {
            StringBuilder sb = new StringBuilder("接收到广播:\n");
            String action = intent.getAction();
            sb.append("action: ");
            sb.append(action);
            String $2 = "\n";
            sb.append($2);
            sb.append("extras:\n");
            Bundle extras = intent.getExtras();
            if (extras != null) {
                for (String str : extras.keySet()) {
                    sb.append("    ");
                    sb.append(str);
                    sb.append(" : ");
                    sb.append(extras.get(str));
                    sb.append($2);
                }
            }
            int intExtra = intent.getIntExtra("pid", -1);
            sb.append("fromPid : ");
            sb.append(intExtra);
            sb.append($2);
            if (intExtra == BroadcastTestActivity.this.f22702a) {
                sb.append("这是自己发送的广播\n");
            } else {
                int uidByPid = VActivityManager.get().getUidByPid(intExtra);
                sb.append("fromUid : ");
                sb.append(uidByPid);
                sb.append($2);
                int v5 = VUserHandle.v(uidByPid);
                sb.append("fromUserId : ");
                sb.append(v5);
                sb.append($2);
            }
            Log.e("VA", "recv info: \n" + ((Object) sb));
            BroadcastTestActivity.this.f22705d.setText(sb);
        }
    }

    

    static {
        StubApp.interface11(3247);
        
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void c(int i5) {
        Intent intent = new Intent(this.f22706e + "_" + i5);
        intent.putExtra("pid", this.f22702a);
        intent.putExtra("toPid", i5);
        intent.putExtra("randomMsg", b());
        intent.putExtra("pkg", getPackageName());
        intent.putExtra("tpPkg", this.f22703b.getText());
        this.f22705d.setText("叚逊年撦1+" + intent.getAction());
        sendBroadcast(intent);
    }

    public String b() {
        return Integer.toString(this.f22704c.nextInt());
    }

    @Override // android.app.Activity
    protected native void onCreate(@k0 Bundle bundle);

    @Override // android.app.Activity
    protected void onDestroy() {
        super.onDestroy();
        unregisterReceiver(this.f22708g);
    }
}
