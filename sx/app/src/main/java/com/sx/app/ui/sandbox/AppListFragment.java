package com.sx.app.ui.sandbox;

import android.content.Intent;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import com.google.android.material.floatingactionbutton.FloatingActionButton;
import com.sx.app.R;
import com.sx.app.data.SandboxAppInfo;
import com.sx.app.sandbox.SandboxProvider;
import com.sx.app.ui.MainActivity;
import java.util.List;

public class AppListFragment extends Fragment {

    private RecyclerView mRvApps;
    private TextView mTvEmpty;
    private SandboxAppAdapter mAdapter;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_app_list, container, false);

        mRvApps = view.findViewById(R.id.rv_apps);
        mTvEmpty = view.findViewById(R.id.tv_empty);
        FloatingActionButton fabAdd = view.findViewById(R.id.fab_add);

        // Hide toolbar if hosted in MainActivity
        if (getActivity() instanceof MainActivity) {
            View appBar = view.findViewById(R.id.app_bar);
            if (appBar != null) {
                appBar.setVisibility(View.GONE);
            }
        } else {
            // Set up toolbar back button if in AppListActivity
            androidx.appcompat.widget.Toolbar toolbar = view.findViewById(R.id.toolbar);
            if (toolbar != null && getActivity() != null) {
                toolbar.setNavigationIcon(android.R.drawable.ic_menu_revert);
                toolbar.setNavigationOnClickListener(v -> getActivity().finish());
            }
        }

        mRvApps.setLayoutManager(new LinearLayoutManager(getContext()));
        mAdapter = new SandboxAppAdapter(getContext());
        mRvApps.setAdapter(mAdapter);

        fabAdd.setOnClickListener(v -> {
            startActivity(new Intent(getContext(), AppPickerActivity.class));
        });

        return view;
    }

    @Override
    public void onResume() {
        super.onResume();
        refreshList();
    }

    private void refreshList() {
        if (getContext() == null || mAdapter == null) return;
        List<SandboxAppInfo> list = SandboxProvider.getEngine().listInstalled();
        mAdapter.setList(list);
        if (list.isEmpty()) {
            mTvEmpty.setVisibility(View.VISIBLE);
            mRvApps.setVisibility(View.GONE);
        } else {
            mTvEmpty.setVisibility(View.GONE);
            mRvApps.setVisibility(View.VISIBLE);
        }
    }
}
