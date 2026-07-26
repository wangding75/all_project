package com.sx.app.ui.sandbox;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.ProgressBar;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import com.sx.app.R;
import com.sx.app.sandbox.HostAppInfo;
import com.sx.app.sandbox.HostAppScanner;
import com.sx.app.sandbox.InstallResult;
import com.sx.app.sandbox.SandboxProvider;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class AppPickerActivity extends AppCompatActivity {

    private final ExecutorService mExecutor = Executors.newSingleThreadExecutor();
    private final Handler mMainHandler = new Handler(Looper.getMainLooper());
    
    private ProgressBar mProgress;
    private RecyclerView mRvApps;
    private HostAppAdapter mAdapter;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_app_picker);

        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
            getSupportActionBar().setTitle(R.string.action_add_app);
        }
        toolbar.setNavigationOnClickListener(v -> finish());

        mProgress = findViewById(R.id.progress);
        mRvApps = findViewById(R.id.rv_apps);

        mRvApps.setLayoutManager(new LinearLayoutManager(this));
        mAdapter = new HostAppAdapter(this, info -> installApp(info));
        mRvApps.setAdapter(mAdapter);

        loadApps();
    }

    private void loadApps() {
        mProgress.setVisibility(View.VISIBLE);
        mRvApps.setVisibility(View.GONE);

        mExecutor.execute(() -> {
            HostAppScanner scanner = new HostAppScanner();
            List<HostAppInfo> apps = scanner.loadLaunchableApps(AppPickerActivity.this);
            mMainHandler.post(() -> {
                if (isFinishing() || isDestroyed()) {
                    return;
                }
                mProgress.setVisibility(View.GONE);
                mRvApps.setVisibility(View.VISIBLE);
                mAdapter.setList(apps);
                if (apps.isEmpty()) {
                    Toast.makeText(AppPickerActivity.this, "未找到可导入的应用，请检查 QUERY_ALL_PACKAGES 权限（系统可能限制包可见性）", Toast.LENGTH_LONG).show();
                }
            });
        });
    }

    private void installApp(HostAppInfo info) {
        mProgress.setVisibility(View.VISIBLE);
        mExecutor.execute(() -> {
            InstallResult result = SandboxProvider.getEngine().installFromHost(info.packageName);
            mMainHandler.post(() -> {
                if (isFinishing() || isDestroyed()) {
                    return;
                }
                mProgress.setVisibility(View.GONE);
                if (result.success) {
                    Toast.makeText(AppPickerActivity.this, "导入成功", Toast.LENGTH_SHORT).show();
                    finish();
                } else {
                    Toast.makeText(AppPickerActivity.this, "导入失败: " + result.message, Toast.LENGTH_LONG).show();
                }
            });
        });
    }

    @Override
    protected void onDestroy() {
        mExecutor.shutdown();
        super.onDestroy();
    }
}
