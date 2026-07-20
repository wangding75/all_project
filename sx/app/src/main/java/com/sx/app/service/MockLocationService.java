package com.sx.app.service;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.util.Log;

public class MockLocationService extends Service {
    private static final String TAG = "MockLocationService";

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Log.d(TAG, "MockLocationService started and stopped immediately (Phase 0 empty stub)");
        stopSelf();
        return START_NOT_STICKY;
    }
}
