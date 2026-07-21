package com.sx.app.sandbox;

import android.graphics.drawable.Drawable;

public class HostAppInfo {
    public String packageName;
    public String label;
    public Drawable icon;
    public String sourceDir;

    public HostAppInfo(String packageName, String label, Drawable icon, String sourceDir) {
        this.packageName = packageName;
        this.label = label;
        this.icon = icon;
        this.sourceDir = sourceDir;
    }
}
