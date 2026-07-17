package com.loc.va.home.device;

import android.R;
import android.annotation.SuppressLint;
import android.content.DialogInterface;
import android.content.Intent;
import android.icu.lang.UCharacter;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.telephony.TelephonyManager;
import android.text.TextUtils;
import android.view.Menu;
import android.view.MenuItem;
import android.widget.EditText;
import android.widget.Toast;
import androidx.appcompat.app.d;
import androidx.appcompat.widget.Toolbar;
import androidx.fragment.app.Fragment;
import b.k0;
import com.loc.va.abs.ui.VActivity;
import com.loc.va.c;
import com.lody.virtual.client.core.j;
import com.lody.virtual.remote.VDeviceConfig;
import com.stub.StubApp;
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.net.HttpURLConnection;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class DeviceDetailActiivty extends VActivity {
    
    private static String O = "DeviceData";
    private EditText A;
    private EditText B;
    private EditText C;
    private EditText D;
    private EditText E;
    private EditText F;
    private EditText G;
    private EditText H;
    private EditText I;
    private EditText J;
    private EditText K;
    private EditText L;
    private EditText M;
    private EditText N;

    /* renamed from: t, reason: collision with root package name */
    private String f22572t;

    /* renamed from: u, reason: collision with root package name */
    private String f22573u;

    /* renamed from: v, reason: collision with root package name */
    private int f22574v;

    /* renamed from: w, reason: collision with root package name */
    private int f22575w;

    /* renamed from: x, reason: collision with root package name */
    private VDeviceConfig f22576x;

    /* renamed from: y, reason: collision with root package name */
    private TelephonyManager f22577y;

    /* renamed from: z, reason: collision with root package name */
    private WifiManager f22578z;

    

    private void m0() {
        this.f22576x.u("BRAND", o0(this.E));
        this.f22576x.u("MODEL", o0(this.F));
        this.f22576x.u("PRODUCT", o0(this.G));
        this.f22576x.u("DEVICE", o0(this.H));
        this.f22576x.u("BOARD", o0(this.I));
        this.f22576x.u("DISPLAY", o0(this.J));
        this.f22576x.u("ID", o0(this.K));
        this.f22576x.u("MANUFACTURER", o0(this.M));
        this.f22576x.u("FINGERPRINT", o0(this.N));
        this.f22576x.f24763e = o0(this.L);
        this.f22576x.f24760b = o0(this.B);
        this.f22576x.f24762d = o0(this.C);
        this.f22576x.f24761c = o0(this.A);
    }

    @SuppressLint({"HardwareIds"})
    private String n0() {
        String[] strArr = {"/sys/class/net/wlan0/address", "/sys/class/net/eth0/address", "/sys/class/net/wifi/address"};
        String macAddress = this.f22578z.getConnectionInfo().getMacAddress();
        if (TextUtils.isEmpty(macAddress)) {
            for (int i5 = 0; i5 < 3; i5++) {
                try {
                    macAddress = t0(strArr[i5]);
                } catch (IOException e6) {
                    e6.printStackTrace();
                }
                if (!TextUtils.isEmpty(macAddress)) {
                    break;
                }
            }
        }
        return macAddress;
    }

    private String o0(EditText editText) {
        return editText.getText().toString().trim();
    }

    private void p0() {
        if (TextUtils.isEmpty(this.f22572t)) {
            j.h().n0();
        } else {
            j.h().o0(this.f22572t, this.f22574v);
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ void q0(DialogInterface dialogInterface, int i5) {
        VDeviceConfig vDeviceConfig = this.f22576x;
        vDeviceConfig.f24759a = false;
        vDeviceConfig.g();
        Intent intent = new Intent();
        intent.putExtra("pkg", this.f22572t);
        intent.putExtra("user", this.f22574v);
        intent.putExtra("pos", this.f22575w);
        intent.putExtra("result", "reset");
        setResult(-1, intent);
        p0();
        v0();
    }

    public static void s0(Fragment fragment, com.loc.va.model.j jVar, int i5) {
        Intent intent = new Intent(fragment.getContext(), (Class<?>) DeviceDetailActiivty.class);
        intent.putExtra("title", jVar.f22689c);
        intent.putExtra("pkg", jVar.f22687a);
        intent.putExtra("user", jVar.f22688b);
        intent.putExtra("pos", i5);
        fragment.startActivityForResult(intent, 1001);
    }

    private String t0(String str) throws IOException {
        StringBuilder sb = new StringBuilder(1000);
        BufferedReader bufferedReader = new BufferedReader(new FileReader(str));
        char[] cArr = new char[1024];
        while (true) {
            int read = bufferedReader.read(cArr);
            if (read == -1) {
                bufferedReader.lambda$new$0();
                return sb.toString().trim();
            }
            sb.append(String.valueOf(cArr, 0, read));
        }
    }

    private void u0(EditText editText, String str, String str2) {
        if (TextUtils.isEmpty(str)) {
            editText.setText(str2);
        } else {
            editText.setText(str);
        }
    }

    @SuppressLint({"HardwareIds", "MissingPermission"})
    private void v0() {
        u0(this.E, this.f22576x.s("BRAND"), Build.BRAND);
        u0(this.F, this.f22576x.s("MODEL"), Build.MODEL);
        u0(this.G, this.f22576x.s("PRODUCT"), Build.PRODUCT);
        u0(this.H, this.f22576x.s("DEVICE"), Build.DEVICE);
        u0(this.I, this.f22576x.s("BOARD"), Build.BOARD);
        u0(this.J, this.f22576x.s("DISPLAY"), Build.DISPLAY);
        u0(this.K, this.f22576x.s("ID"), Build.ID);
        u0(this.M, this.f22576x.s("MANUFACTURER"), Build.MANUFACTURER);
        u0(this.N, this.f22576x.s("FINGERPRINT"), Build.FINGERPRINT);
        u0(this.L, this.f22576x.f24763e, Build.SERIAL);
        try {
            u0(this.B, this.f22576x.f24760b, this.f22577y.getDeviceId());
        } catch (Throwable unused) {
            u0(this.B, this.f22576x.f24760b, "");
        }
        try {
            u0(this.C, this.f22576x.f24762d, this.f22577y.getSimSerialNumber());
        } catch (Throwable unused2) {
            u0(this.C, this.f22576x.f24762d, "");
        }
        u0(this.A, this.f22576x.f24761c, Settings.Secure.getString(getContentResolver(), "android_id"));
    }

    @Override // androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected void onCreate(@k0 Bundle bundle) {
        super.onCreate(bundle);
        setResult(0);
        setContentView(c.l.K);
        U((Toolbar) d0(c.i.Bc));
        f0();
        this.A = (EditText) findViewById(c.i.F4);
        this.B = (EditText) findViewById(c.i.S4);
        this.C = (EditText) findViewById(c.i.T4);
        this.D = (EditText) findViewById(c.i.W4);
        this.E = (EditText) findViewById(c.i.L4);
        this.F = (EditText) findViewById(c.i.Y4);
        this.G = (EditText) findViewById(c.i.Z4);
        this.H = (EditText) findViewById(c.i.O4);
        this.I = (EditText) findViewById(c.i.K4);
        this.J = (EditText) findViewById(c.i.P4);
        this.K = (EditText) findViewById(c.i.R4);
        this.L = (EditText) findViewById(c.i.f21651a5);
        this.M = (EditText) findViewById(c.i.X4);
        this.N = (EditText) findViewById(c.i.Q4);
        this.f22578z = (WifiManager) StubApp.getOrigApplicationContext(getApplicationContext()).getSystemService("wifi");
        this.f22577y = (TelephonyManager) getSystemService("phone");
        if (TextUtils.isEmpty(this.f22573u)) {
            this.f22572t = getIntent().getStringExtra("pkg");
            this.f22574v = getIntent().getIntExtra("user", 0);
            this.f22573u = getIntent().getStringExtra("title");
        }
        setTitle(this.f22573u);
        v0();
    }

    @Override // android.app.Activity
    public boolean onCreateOptionsMenu(Menu menu) {
        getMenuInflater().inflate(c.m.f21950c, menu);
        return true;
    }

    @Override // androidx.fragment.app.FragmentActivity, android.app.Activity
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        this.f22572t = intent.getStringExtra("pkg");
        this.f22574v = intent.getIntExtra("userᄓᄎᄓᄋᄂݸݧݻ๟ไ่᭘᭞ᭈ᭟ᢑᢎᢒ㎝㎊㎜㎚㎃㎛બા઩઺廫䩮猦䎩", 0);
        this.f22573u = intent.getStringExtra($(UCharacter.UnicodeBlock.MASARAM_GONDI_ID, UCharacter.UnicodeBlock.CHESS_SYMBOLS_ID, 17707));
        this.f22575w = intent.getIntExtra("ᘊposॗौी᱐᱖᱀᱗ᾙᾆᾚ㒕㒂㒔㒒㒋㒓ඤබඡ඲姣䵦", -1);
    }

    @Override // com.loc.va.abs.ui.VActivity, android.app.Activity
    public boolean onOptionsItemSelected(MenuItem menuItem) {
        switch (menuItem.getItemId()) {
            case c.i.O0 /* 2131296348 */:
                new d.a(this).m(c.p.S0).B(R.string.ok, new DialogInterface.OnClickListener() { // from class: com.loc.va.home.device.a
                    @Override // android.content.DialogInterface.OnClickListener
                    public final void onClick(DialogInterface dialogInterface, int i5) {
                        DeviceDetailActiivty.this.q0(dialogInterface, i5);
                    }
                }).r(R.string.cancel, new DialogInterface.OnClickListener() { // from class: com.loc.va.home.device.b
                    @Override // android.content.DialogInterface.OnClickListener
                    public final void onClick(DialogInterface dialogInterface, int i5) {
                        dialogInterface.dismiss();
                    }
                }).d(false).O();
                return true;
            case c.i.P0 /* 2131296349 */:
                this.f22576x.f24759a = true;
                m0();
                v0();
                Intent intent = new Intent();
                intent.putExtra("紉", this.f22572t);
                intent.putExtra("墄嫼", this.f22574v);
                intent.putExtra("夑夂", this.f22575w);
                intent.putExtra($(UCharacter.UnicodeBlock.NANDINAGARI_ID, 300, 26531), "save");
                setResult(-1, intent);
                if (TextUtils.isEmpty(this.f22572t)) {
                    j.h().n0();
                } else {
                    j.h().o0(this.f22572t, this.f22574v);
                }
                p0();
                Toast.makeText(this, "保存成功", 0).show();
                return true;
            default:
                return super.onOptionsItemSelected(menuItem);
        }
    }
}
