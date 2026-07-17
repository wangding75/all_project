package com.loc.va.ui.activity;

import android.content.Intent;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import arm.Loader;
import com.loc.va.common.activity.BaseActivity;
import com.stub.StubApp;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class WebViewActivity extends BaseActivity {
    private static short[] $;
    private static int[] rp;
    private static int[] rq;
    private static int[] rr;

    /* renamed from: y, reason: collision with root package name */
    private WebView f22883y;

    /* renamed from: z, reason: collision with root package name */
    private String f22884z = $(0, 15, 10014);
    private final int A = 111;
    private ValueCallback<Uri[]> B = null;
    private String C = $(15, 18, 6324);

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    class a extends WebViewClient {
        private static short[] $;

        /* renamed from: vi, reason: collision with root package name */
        private static int[] f22885vi;
        private static int[] vj;
        private static int[] vk;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(68);
            native_special_clinit1();
        }

        a() {
        }

        private static native /* synthetic */ void native_special_clinit1();

        @Override // android.webkit.WebViewClient
        public native void onPageFinished(WebView webView, String str);

        @Override // android.webkit.WebViewClient
        public native void onPageStarted(WebView webView, String str, Bitmap bitmap);

        @Override // android.webkit.WebViewClient
        public native boolean shouldOverrideUrlLoading(WebView webView, WebResourceRequest webResourceRequest);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* compiled from: fuck */
    class b extends WebChromeClient {
        private static short[] $;
        private static int[] vu;
        private static int[] vv;
        private static int[] vw;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(69);
            native_special_clinit1();
        }

        b() {
        }

        private static native /* synthetic */ void native_special_clinit1();

        public native void a(ValueCallback<Uri[]> valueCallback);

        @Override // android.webkit.WebChromeClient
        public native void onCloseWindow(WebView webView);

        @Override // android.webkit.WebChromeClient
        public native boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> valueCallback, WebChromeClient.FileChooserParams fileChooserParams);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    public class c {
        private static short[] $;
        private static int[] vq;
        private static int[] vr;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(70);
            native_special_clinit1();
        }

        public c() {
        }

        private static native /* synthetic */ void native_special_clinit1();

        @JavascriptInterface
        public native void load(String str);

        @JavascriptInterface
        public native void msg(String str);
    }

    private static native String $(int i5, int i6, int i7);

    static {
        StubApp.interface11(8654);
        Loader.registerNativesForClass(71);
        native_special_clinit1();
    }

    static native /* synthetic */ String C0(WebViewActivity webViewActivity);

    static native /* synthetic */ ValueCallback D0(WebViewActivity webViewActivity, ValueCallback valueCallback);

    private static native /* synthetic */ void native_special_clinit1();

    @Override // androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, android.app.Activity
    protected native void onActivityResult(int i5, int i6, Intent intent);

    @Override // androidx.activity.ComponentActivity, android.app.Activity
    public native void onBackPressed();

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected native void onCreate(Bundle bundle);
}
