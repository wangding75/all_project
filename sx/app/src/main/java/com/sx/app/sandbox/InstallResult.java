package com.sx.app.sandbox;

public class InstallResult {
    public boolean success;
    public int userId;
    public String message;

    public InstallResult(boolean success, int userId, String message) {
        this.success = success;
        this.userId = userId;
        this.message = message;
    }
}
