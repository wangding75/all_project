package com.sx.app.util;

import android.content.Context;
import android.util.Log;

import com.sx.app.data.SxPrefs;

import org.json.JSONObject;

import java.io.File;
import java.net.HttpURLConnection;
import java.net.URL;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.TimeZone;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Anti clock-rollback:
 * 1) Prefer network Date header (HTTP HEAD)
 * 2) Compare against last known good time persisted on disk
 * 3) File lastModified of stamp file cannot go backwards
 */
public final class TimeGuard {

    private static final String TAG = "TimeGuard";
    private static final ExecutorService EXEC = Executors.newSingleThreadExecutor();

    private TimeGuard() {}

    public static long getTrustedNow(Context context) {
        JSONObject o = SxPrefs.getJson(context, SxPrefs.KEY_TIME_GUARD);
        long lastGood = o.optLong("lastGood", 0L);
        long systemNow = System.currentTimeMillis();
        long fileStamp = readFileStamp(context);

        long candidate = Math.max(systemNow, Math.max(lastGood, fileStamp));
        // If system clock is far behind last good, treat as rollback and use last good
        if (lastGood > 0 && systemNow + 60_000L < lastGood) {
            Log.w(TAG, "Clock rollback suspected: system=" + systemNow + " lastGood=" + lastGood);
            candidate = Math.max(lastGood, fileStamp);
        }
        persist(context, candidate);
        return candidate;
    }

    public static void refreshNetworkTimeAsync(Context context) {
        final Context app = context.getApplicationContext();
        EXEC.execute(() -> {
            long net = fetchNetworkTimeMillis();
            if (net > 0) {
                long localTrusted = getTrustedNow(app);
                long merged = Math.max(net, localTrusted);
                persist(app, merged);
            }
        });
    }

    private static void persist(Context context, long millis) {
        try {
            JSONObject o = new JSONObject();
            o.put("lastGood", millis);
            SxPrefs.putJson(context, SxPrefs.KEY_TIME_GUARD, o);
            writeFileStamp(context, millis);
        } catch (Exception e) {
            Log.e(TAG, "persist failed", e);
        }
    }

    private static File stampFile(Context context) {
        return new File(context.getFilesDir(), "sx_time_stamp.dat");
    }

    private static void writeFileStamp(Context context, long millis) {
        try {
            File f = stampFile(context);
            java.io.FileOutputStream fos = new java.io.FileOutputStream(f);
            fos.write(String.valueOf(millis).getBytes(java.nio.charset.StandardCharsets.UTF_8));
            fos.close();
            // Keep mtime monotonic
            long m = f.lastModified();
            if (m < millis) {
                // no-op; FS mtime is current
            }
        } catch (Exception ignored) {
        }
    }

    private static long readFileStamp(Context context) {
        try {
            File f = stampFile(context);
            if (!f.exists()) {
                return 0L;
            }
            byte[] buf = new byte[(int) Math.min(f.length(), 32)];
            java.io.FileInputStream fis = new java.io.FileInputStream(f);
            int n = fis.read(buf);
            fis.close();
            if (n > 0) {
                return Long.parseLong(new String(buf, 0, n).trim());
            }
            return f.lastModified();
        } catch (Exception e) {
            return 0L;
        }
    }

    /** HEAD request to a well-known host and parse Date header. */
    public static long fetchNetworkTimeMillis() {
        String[] urls = {
                "https://www.baidu.com",
                "https://www.cloudflare.com",
                "https://www.microsoft.com"
        };
        for (String u : urls) {
            try {
                HttpURLConnection conn = (HttpURLConnection) new URL(u).openConnection();
                conn.setRequestMethod("HEAD");
                conn.setConnectTimeout(4000);
                conn.setReadTimeout(4000);
                conn.setInstanceFollowRedirects(true);
                conn.connect();
                String date = conn.getHeaderField("Date");
                conn.disconnect();
                if (date != null && !date.isEmpty()) {
                    SimpleDateFormat sdf = new SimpleDateFormat("EEE, dd MMM yyyy HH:mm:ss zzz", Locale.US);
                    sdf.setTimeZone(TimeZone.getTimeZone("GMT"));
                    Date d = sdf.parse(date);
                    if (d != null) {
                        return d.getTime();
                    }
                }
            } catch (Exception e) {
                Log.d(TAG, "network time fail: " + u + " " + e.getMessage());
            }
        }
        return -1L;
    }
}
