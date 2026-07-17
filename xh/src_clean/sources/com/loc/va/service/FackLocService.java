package com.loc.va.service;

import android.annotation.SuppressLint;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.icu.lang.UCharacter;
import android.location.Location;
import android.location.LocationManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.IBinder;
import android.os.Looper;
import android.os.Message;
import android.os.SystemClock;
import android.util.Log;
import android.widget.Toast;
import com.baidu.mapapi.model.LatLng;
import com.stub.StubApp;
import java.util.UUID;
import tv.danmaku.ijk.media.player.i;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class FackLocService extends Service {
    

    /* renamed from: g, reason: collision with root package name */
    public static final int f22691g = 1;

    /* renamed from: h, reason: collision with root package name */
    public static final int f22692h = 2;

    /* renamed from: i, reason: collision with root package name */
    public static boolean f22693i;

    /* renamed from: b, reason: collision with root package name */
    public Handler f22695b;

    /* renamed from: c, reason: collision with root package name */
    private HandlerThread f22696c;

    /* renamed from: e, reason: collision with root package name */
    public LatLng f22698e;

    /* renamed from: f, reason: collision with root package name */
    public LocationManager f22699f;

    /* renamed from: a, reason: collision with root package name */
    public String f22694a = "FackLocService";

    /* renamed from: d, reason: collision with root package name */
    public String f22697d = "113.92966357,22.54346416";

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    class a extends Handler {
        

        /* renamed from: a, reason: collision with root package name */
        final FackLocService f22700a;

        

        a(FackLocService fackLocService, Looper looper) {
            super(looper);
            this.f22700a = fackLocService;
        }

        @Override // android.os.Handler
        public void handleMessage(Message message) {
            try {
                Thread.sleep(50L);
                FackLocService fackLocService = this.f22700a;
                if (FackLocService.f22693i) {
                    fackLocService.k();
                    this.f22700a.h();
                    sendEmptyMessage(0);
                }
            } catch (InterruptedException e6) {
                e6.printStackTrace();
                Log.d(this.f22700a.f22694a, "handleMessage error");
                Thread.currentThread().interrupt();
            }
        }
    }

    

    static {
        StubApp.interface11(8626);
        
    }

    public static String e() {
        return UUID.randomUUID().toString();
    }

    private void f() {
        String $2 = "gps";
        try {
            if (!this.f22699f.isProviderEnabled($2)) {
                Log.d(this.f22694a, "GPSProvider is not enabled");
                return;
            }
            Log.d(this.f22694a, "now remove GPS Provider");
            this.f22699f.clearTestProviderEnabled($2);
            this.f22699f.removeTestProvider($2);
        } catch (Exception e6) {
            e6.printStackTrace();
            Log.d(this.f22694a, "rmGPSProvider error");
        }
    }

    private void g() {
        String $2 = "network";
        try {
            if (!this.f22699f.isProviderEnabled($2)) {
                Log.d(this.f22694a, "NetworkProvider is not enabled");
                return;
            }
            Log.d(this.f22694a, "now remove Network Provider");
            this.f22699f.clearTestProviderEnabled($2);
            this.f22699f.removeTestProvider($2);
        } catch (Exception e6) {
            e6.printStackTrace();
            Log.d(this.f22694a, "rmNetworkProvider error");
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void h() {
        try {
            this.f22699f.setTestProviderLocation("gps", c(this.f22698e));
        } catch (Exception e6) {
            Log.d(this.f22694a, "setGPSLocation error");
            e6.printStackTrace();
        }
    }

    private void i() {
        LocationManager locationManager = this.f22699f;
        String $2 = "gps";
        locationManager.getProvider($2);
        try {
            this.f22699f.addTestProvider("gps", false, true, true, false, true, true, true, 1, 2);
            Log.i(this.f22694a, "addTestProvider[GPS_PROVIDER] success");
        } catch (Exception e6) {
            e6.printStackTrace();
            Log.e(this.f22694a, "addTestProvider[GPS_PROVIDER] errorչկվ՞կ");
        }
        if (!this.f22699f.isProviderEnabled($2)) {
            try {
                this.f22699f.setTestProviderEnabled($2, true);
            } catch (Exception e7) {
                e7.printStackTrace();
                Log.e(this.f22694a, "stProviderEnabled[GPS_PROVIDER] error");
            }
        }
        this.f22699f.setTestProviderStatus("gps", 2, null, System.currentTimeMillis());
    }

    private void j() {
        try {
            this.f22699f.addTestProvider("network", false, false, false, false, false, false, false, 1, 1);
            Log.d(this.f22694a, "addTestProvider[NETWORK_PROVIDER] success");
        } catch (SecurityException e6) {
            e6.printStackTrace();
            Log.d(this.f22694a, "addTestProvider[NETWORK_PROVIDER] error");
        }
        LocationManager locationManager = this.f22699f;
        String $2 = "network";
        if (locationManager.isProviderEnabled($2)) {
            return;
        }
        try {
            this.f22699f.setTestProviderEnabled($2, true);
        } catch (Exception e7) {
            e7.printStackTrace();
            Log.d(this.f22694a, "setTestProviderEnabled[NETWORK_PROVIDER] error");
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void k() {
        try {
            this.f22699f.setTestProviderLocation("network", c(this.f22698e));
        } catch (Exception e6) {
            Log.d(this.f22694a, "setNetworkLocation error");
            e6.printStackTrace();
        }
    }

    public Location c(LatLng latLng) {
        Location location = new Location("ᵸᵯᵬ");
        location.setSpeed(0.0f);
        location.setAccuracy(2.0f);
        location.setAltitude(55.0d);
        location.setBearing(1.0f);
        Bundle bundle = new Bundle();
        bundle.putInt("satellites", 7);
        location.setExtras(bundle);
        location.setLatitude(latLng.latitude);
        location.setLongitude(latLng.longitude);
        location.setTime(System.currentTimeMillis());
        location.setElapsedRealtimeNanos(SystemClock.elapsedRealtimeNanos());
        return location;
    }

    public void d() {
        for (String str : this.f22699f.getProviders(true)) {
            Log.d(this.f22694a, "PROV--->" + str);
        }
    }

    public void l(String str) {
        Toast.makeText(this, str, 1).show();
    }

    @Override // android.app.Service
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override // android.app.Service
    @SuppressLint({"WrongConstant"})
    public void onCreate() {
        Log.d(this.f22694a, "onCreate");
        super.onCreate();
        this.f22699f = (LocationManager) getSystemService("location");
        d();
        g();
        f();
        j();
        i();
        HandlerThread handlerThread = new HandlerThread(e(), -2);
        this.f22696c = handlerThread;
        handlerThread.start();
        a aVar = new a(this, this.f22696c.getLooper());
        this.f22695b = aVar;
        aVar.sendEmptyMessage(0);
    }

    @Override // android.app.Service
    public void onDestroy() {
        Log.d(this.f22694a, "onDestroy");
        f22693i = false;
        this.f22695b.removeMessages(0);
        this.f22696c.quit();
        g();
        f();
        stopForeground(true);
        super.onDestroy();
    }

    @Override // android.app.Service
    public void onStart(Intent intent, int i5) {
        super.onStart(intent, i5);
        Log.d(this.f22694a, "onStart");
    }

    @Override // android.app.Service
    public int onStartCommand(Intent intent, int i5, int i6) {
        String notificationChannel;
        Notification.Builder channelId;
        Log.d(this.f22694a, "onStartCommand");
        NotificationManager notificationManager = (NotificationManager) getSystemService("notification");
        if (Build.VERSION.SDK_INT >= 26) {
            String $2 = "channel_name";
            String $3 = "channel_01";
            NotificationChannel notificationChannel2 = new NotificationChannel($3, $2, 2);
            String str = this.f22694a;
            notificationChannel = notificationChannel2.toString();
            Log.i(str, notificationChannel);
            if (notificationManager != null) {
                notificationManager.createNotificationChannel(notificationChannel2);
            }
            channelId = new Notification.Builder(this).setChannelId($3);
            startForeground(1, channelId.setContentTitle("位置模拟服务已启动").setContentText("MockLocation service is running").setSmallIcon(getApplicationInfo().icon).build());
        }
        String stringExtra = intent.getStringExtra("key");
        this.f22697d = stringExtra;
        String[] split = stringExtra.split(",");
        this.f22698e = new LatLng(Double.valueOf(split[1]).doubleValue(), Double.valueOf(split[0]).doubleValue());
        Log.d(this.f22694a, "DataFromMain is " + this.f22697d);
        f22693i = true;
        return super.onStartCommand(intent, i5, i6);
    }
}
