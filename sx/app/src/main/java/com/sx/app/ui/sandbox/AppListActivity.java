package com.sx.app.ui.sandbox;

import android.os.Bundle;
import androidx.appcompat.app.AppCompatActivity;

public class AppListActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (savedInstanceState == null) {
            getSupportFragmentManager().beginTransaction()
                    .replace(android.R.id.content, new AppListFragment())
                    .commit();
        }
    }
}
