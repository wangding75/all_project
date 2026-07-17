package com.loc.va.ui.activity;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

/**
 * 激活/登录页 Activity
 * 功能：
 *   1. 输入激活码验证（付费功能）
 *   2. 账号/邮箱+验证码 登录
 *   3. 新用户注册（免费试用 3 天）
 *   4. 忘记密码/重置密码
 *
 * 原始类名：com.loc.va.ui.activity.ActiveCardActivity
 */
public class ActiveCardActivity extends Activity {

    private EditText etAccount;
    private EditText etVerifyCode;
    private EditText etActiveCode;
    private Button btnLogin;
    private Button btnGetVerifyCode;
    private TextView tvRegister;
    private TextView tvForgetPassword;

    private int countDownSeconds = 60;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // setContentView(R.layout.activity_active_card);

        initViews();
        initListeners();
    }

    private void initViews() {
        // etAccount = findViewById(R.id.et_account);
        // etVerifyCode = findViewById(R.id.et_verify_code);
        // etActiveCode = findViewById(R.id.et_active_code);
        // btnLogin = findViewById(R.id.btn_login);
        // btnGetVerifyCode = findViewById(R.id.btn_get_verify_code);
        // tvRegister = findViewById(R.id.tv_register);
        // tvForgetPassword = findViewById(R.id.tv_forget_password);
    }

    private void initListeners() {
        btnLogin.setOnClickListener(v -> doLogin());
        btnGetVerifyCode.setOnClickListener(v -> getVerifyCode());
        tvRegister.setOnClickListener(v -> doRegister());
        tvForgetPassword.setOnClickListener(v -> resetPassword());
    }

    /**
     * 使用账号+验证码登录
     */
    private void doLogin() {
        String account = etAccount.getText().toString().trim();
        String code = etVerifyCode.getText().toString().trim();
        String activeCode = etActiveCode.getText().toString().trim();

        if (account.isEmpty()) {
            Toast.makeText(this, "邮箱或手机号不能为空", Toast.LENGTH_SHORT).show();
            return;
        }

        if (code.isEmpty()) {
            Toast.makeText(this, "验证码不能为空", Toast.LENGTH_SHORT).show();
            return;
        }

        // 发起网络请求验证
        requestLogin(account, code, activeCode);
    }

    /**
     * 获取手机验证码
     */
    private void getVerifyCode() {
        String account = etAccount.getText().toString().trim();
        if (account.isEmpty()) {
            Toast.makeText(this, "请先输入手机号或邮箱", Toast.LENGTH_SHORT).show();
            return;
        }

        // 发起网络请求获取验证码
        requestVerifyCode(account);
        startCountDown();
    }

    private void startCountDown() {
        // 60秒倒计时，防止频繁获取验证码
        // btnGetVerifyCode.setEnabled(false);
        // new CountDownTimer(60000, 1000) { ... }.start();
    }

    private void doRegister() {
        // 新用户注册，系统免费试用3天
        // Toast.makeText(this, "新用户系统免费试用3天", Toast.LENGTH_SHORT).show();
    }

    private void resetPassword() {
        // 重置密码
    }

    private void requestLogin(String account, String code, String activeCode) {
        // 网络请求示意：POST /api/login
        // 请求成功后保存 token，跳转主页
        // onLoginSuccess();
    }

    private void requestVerifyCode(String account) {
        // 网络请求示意：POST /api/send_code
    }

    private void onLoginSuccess(String token) {
        // 保存登录信息
        getSharedPreferences("user_info", MODE_PRIVATE)
                .edit()
                .putString("token", token)
                .apply();

        // 跳转主页
        startActivity(new Intent(this, HomeActivity.class));
        finish();
    }
}
