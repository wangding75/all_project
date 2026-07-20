package com.sx.app.ui;

import android.os.Bundle;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import androidx.fragment.app.Fragment;
import com.google.android.material.bottomnavigation.BottomNavigationView;
import com.sx.app.R;
import com.sx.app.ui.home.HomeFragment;
import com.sx.app.ui.me.MeFragment;
import com.sx.app.ui.sandbox.AppListFragment;

public class MainActivity extends AppCompatActivity {

    private Toolbar mToolbar;
    private HomeFragment mHomeFragment;
    private AppListFragment mAppListFragment;
    private MeFragment mMeFragment;
    private Fragment mActiveFragment;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        mToolbar = findViewById(R.id.toolbar);
        setSupportActionBar(mToolbar);

        BottomNavigationView bottomNav = findViewById(R.id.bottom_nav);
        bottomNav.setOnItemSelectedListener(item -> {
            int itemId = item.getItemId();
            if (itemId == R.id.nav_home) {
                switchFragment(mHomeFragment);
                mToolbar.setTitle(R.string.app_name_full);
                return true;
            } else if (itemId == R.id.nav_apps) {
                switchFragment(mAppListFragment);
                mToolbar.setTitle(R.string.module_sandbox);
                return true;
            } else if (itemId == R.id.nav_me) {
                switchFragment(mMeFragment);
                mToolbar.setTitle(R.string.tab_me);
                return true;
            }
            return false;
        });

        // Initialize and setup fragments (handle config change / process restore)
        if (savedInstanceState == null) {
            mHomeFragment = new HomeFragment();
            mAppListFragment = new AppListFragment();
            mMeFragment = new MeFragment();
            mActiveFragment = mHomeFragment;
            getSupportFragmentManager().beginTransaction()
                    .add(R.id.fragment_container, mHomeFragment, "home")
                    .add(R.id.fragment_container, mAppListFragment, "apps").hide(mAppListFragment)
                    .add(R.id.fragment_container, mMeFragment, "me").hide(mMeFragment)
                    .commit();
            mToolbar.setTitle(R.string.app_name_full);
        } else {
            mHomeFragment = (HomeFragment) getSupportFragmentManager().findFragmentByTag("home");
            mAppListFragment = (AppListFragment) getSupportFragmentManager().findFragmentByTag("apps");
            mMeFragment = (MeFragment) getSupportFragmentManager().findFragmentByTag("me");

            // Tags missing: re-add full set (do not leave detached new instances)
            if (mHomeFragment == null || mAppListFragment == null || mMeFragment == null) {
                mHomeFragment = new HomeFragment();
                mAppListFragment = new AppListFragment();
                mMeFragment = new MeFragment();
                mActiveFragment = mHomeFragment;
                getSupportFragmentManager().beginTransaction()
                        .replace(R.id.fragment_container, mHomeFragment, "home")
                        .add(R.id.fragment_container, mAppListFragment, "apps").hide(mAppListFragment)
                        .add(R.id.fragment_container, mMeFragment, "me").hide(mMeFragment)
                        .commit();
                mToolbar.setTitle(R.string.app_name_full);
            } else {
                // Align visibility with bottom nav after restore (avoid tab/UI desync)
                int selectedId = bottomNav.getSelectedItemId();
                Fragment target;
                int titleRes;
                if (selectedId == R.id.nav_apps) {
                    target = mAppListFragment;
                    titleRes = R.string.module_sandbox;
                } else if (selectedId == R.id.nav_me) {
                    target = mMeFragment;
                    titleRes = R.string.tab_me;
                } else {
                    target = mHomeFragment;
                    titleRes = R.string.app_name_full;
                }
                getSupportFragmentManager().beginTransaction()
                        .hide(mHomeFragment)
                        .hide(mAppListFragment)
                        .hide(mMeFragment)
                        .show(target)
                        .commit();
                mActiveFragment = target;
                mToolbar.setTitle(titleRes);
            }
        }
    }

    private void switchFragment(Fragment fragment) {
        if (fragment == mActiveFragment) return;
        getSupportFragmentManager().beginTransaction()
                .hide(mActiveFragment)
                .show(fragment)
                .commit();
        mActiveFragment = fragment;
    }

    public void switchToAppsTab() {
        BottomNavigationView bottomNav = findViewById(R.id.bottom_nav);
        bottomNav.setSelectedItemId(R.id.nav_apps);
    }
}
