package com.custom.spoofer.service;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.location.Location;
import android.location.LocationManager;
import android.os.Build;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.IBinder;
import android.os.SystemClock;
import android.util.Log;

public class FackLocService extends Service {

    private static final String TAG = "FackLocService";
    private static final String CHANNEL_ID = "SpooferServiceChannel";

    private LocationManager mLocationManager;
    private HandlerThread mHandlerThread;
    private Handler mServiceHandler;
    private boolean isSimulating = false;

    // Default mock coordinates (Shenzhen Hi-Tech Park as example)
    private double mLatitude = 22.543099;
    private double mLongitude = 113.929884;
    private float mAccuracy = 2.0f; // High precision GPS signal

    private final Runnable mSimulationRunnable = new Runnable() {
        @Override
        public void run() {
            if (isSimulating) {
                injectMockLocation();
                // Loop every 50ms to match real-time GPS hardware updates
                mServiceHandler.postDelayed(this, 50);
            }
        }
    };

    @Override
    public void onCreate() {
        super.onCreate();
        mLocationManager = (LocationManager) getSystemService(Context.LOCATION_SERVICE);
        createNotificationChannel();
        Notification notification = buildNotification();
        startForeground(1, notification);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null) {
            mLatitude = intent.getDoubleExtra("latitude", 22.543099);
            mLongitude = intent.getDoubleExtra("longitude", 113.929884);
            mAccuracy = intent.getFloatExtra("accuracy", 2.0f);
            
            String action = intent.getAction();
            if ("STOP".equals(action)) {
                stopSimulating();
                stopSelf();
            } else {
                startSimulating();
            }
        }
        return START_STICKY;
    }

    private void startSimulating() {
        if (!isSimulating) {
            Log.d(TAG, "Starting Mock Location simulation...");
            isSimulating = true;
            mHandlerThread = new HandlerThread("MockLocationThread");
            mHandlerThread.start();
            mServiceHandler = new Handler(mHandlerThread.getLooper());
            
            // Register test provider
            try {
                setupTestProvider(LocationManager.GPS_PROVIDER);
                setupTestProvider(LocationManager.NETWORK_PROVIDER);
            } catch (Exception e) {
                Log.e(TAG, "Failed to setup test providers, check Developer Options Mock Location settings.", e);
            }
            
            mServiceHandler.post(mSimulationRunnable);
        }
    }

    private void stopSimulating() {
        if (isSimulating) {
            Log.d(TAG, "Stopping Mock Location simulation...");
            isSimulating = false;
            if (mServiceHandler != null) {
                mServiceHandler.removeCallbacks(mSimulationRunnable);
            }
            if (mHandlerThread != null) {
                mHandlerThread.quitSafely();
            }
            
            // Clean up test providers
            try {
                mLocationManager.removeTestProvider(LocationManager.GPS_PROVIDER);
                mLocationManager.removeTestProvider(LocationManager.NETWORK_PROVIDER);
            } catch (Exception e) {
                Log.e(TAG, "Error cleaning up mock providers", e);
            }
        }
    }

    private void setupTestProvider(String providerName) {
        mLocationManager.addTestProvider(
                providerName,
                false, // requiresNetwork
                false, // requiresSatellite
                false, // requiresCell
                false, // hasMonetaryCost
                true,  // supportsAltitude
                true,  // supportsSpeed
                true,  // supportsBearing
                0,     // powerRequirement
                1      // accuracy
        );
        mLocationManager.setTestProviderEnabled(providerName, true);
    }

    private void injectMockLocation() {
        try {
            injectLocationForProvider(LocationManager.GPS_PROVIDER);
            injectLocationForProvider(LocationManager.NETWORK_PROVIDER);
        } catch (Exception e) {
            Log.e(TAG, "Error during location injection", e);
        }
    }

    private void injectLocationForProvider(String providerName) {
        Location mockLocation = new Location(providerName);
        mockLocation.setLatitude(mLatitude);
        mockLocation.setLongitude(mLongitude);
        mockLocation.setAccuracy(mAccuracy);
        mockLocation.setTime(System.currentTimeMillis());
        
        // Critical: Set the elapsed real time nanos, otherwise systems will reject it
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
            mockLocation.setElapsedRealtimeNanos(SystemClock.elapsedRealtimeNanos());
        }
        
        mLocationManager.setTestProviderLocation(providerName, mockLocation);
    }

    @Override
    public void onDestroy() {
        stopSimulating();
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel serviceChannel = new NotificationChannel(
                    CHANNEL_ID,
                    "Spoofer Service Channel",
                    NotificationManager.IMPORTANCE_DEFAULT
            );
            NotificationManager manager = getSystemService(NotificationManager.class);
            if (manager != null) {
                manager.createNotificationChannel(serviceChannel);
            }
        }
    }

    private Notification buildNotification() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            return new Notification.Builder(this, CHANNEL_ID)
                    .setContentTitle("Custom Spoofer Active")
                    .setContentText("Injecting mock location in background...")
                    .setSmallIcon(android.R.drawable.ic_menu_mylocation)
                    .build();
        } else {
            return new Notification.Builder(this)
                    .setContentTitle("Custom Spoofer Active")
                    .setContentText("Injecting mock location...")
                    .setSmallIcon(android.R.drawable.ic_menu_mylocation)
                    .build();
        }
    }
}
