package com.sx.app.ui.location;

import android.content.Intent;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import com.sx.app.R;
import java.util.ArrayList;
import java.util.List;

public class LocationPickerActivity extends AppCompatActivity {

    private EditText mEtSearch;
    private RecyclerView mRvPlaces;
    private TextView mTvSelected;
    private PlaceAdapter mAdapter;

    private final List<PlaceAdapter.PlaceInfo> mPresets = new ArrayList<>();
    private final List<PlaceAdapter.PlaceInfo> mFiltered = new ArrayList<>();
    
    private double mSelectedLat = 0;
    private double mSelectedLng = 0;
    private boolean mHasSelection = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_location_picker);

        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
            getSupportActionBar().setTitle(R.string.action_pick_map);
        }
        toolbar.setNavigationOnClickListener(v -> finish());

        mEtSearch = findViewById(R.id.et_search);
        mRvPlaces = findViewById(R.id.rv_places);
        mTvSelected = findViewById(R.id.tv_selected);

        initPresets();

        mRvPlaces.setLayoutManager(new LinearLayoutManager(this));
        mAdapter = new PlaceAdapter(this, info -> {
            mSelectedLat = info.latitude;
            mSelectedLng = info.longitude;
            mHasSelection = true;
            mTvSelected.setText("当前已选: " + info.name + " (" + info.latitude + ", " + info.longitude + ")");
        });
        mRvPlaces.setAdapter(mAdapter);

        mFiltered.addAll(mPresets);
        mAdapter.setList(mFiltered);

        mEtSearch.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                filterPlaces(s.toString());
            }

            @Override
            public void afterTextChanged(Editable s) {}
        });

        mEtSearch.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_SEARCH) {
                filterPlaces(mEtSearch.getText().toString());
                return true;
            }
            return false;
        });

        findViewById(R.id.btn_confirm).setOnClickListener(v -> {
            if (!mHasSelection) {
                Toast.makeText(this, "请先选择一个地点", Toast.LENGTH_SHORT).show();
                return;
            }
            Intent intent = new Intent();
            intent.putExtra("lat", mSelectedLat);
            intent.putExtra("lng", mSelectedLng);
            setResult(RESULT_OK, intent);
            finish();
        });
    }

    private void initPresets() {
        mPresets.add(new PlaceAdapter.PlaceInfo("北京天安门", "北京市东城区东长安街", 39.9087, 116.3975));
        mPresets.add(new PlaceAdapter.PlaceInfo("北京腾讯总部大楼", "北京市海淀区西北旺东路10号院", 40.0403, 116.2736));
        mPresets.add(new PlaceAdapter.PlaceInfo("上海东方明珠", "上海市浦东新区世纪大道1号", 31.2397, 121.4998));
        mPresets.add(new PlaceAdapter.PlaceInfo("上海人民广场", "上海市黄浦区人民大道120号", 31.2318, 121.4726));
        mPresets.add(new PlaceAdapter.PlaceInfo("广州塔 (小蛮腰)", "广东省广州市海珠区阅江西路222号", 23.10647, 113.32446));
        mPresets.add(new PlaceAdapter.PlaceInfo("深圳腾讯大厦 (总部)", "广东省深圳市南山区深南大道10000号", 22.543099, 113.929884));
        mPresets.add(new PlaceAdapter.PlaceInfo("深圳腾讯滨海大厦", "广东省深圳市南山区后海大道与滨海大道交汇处", 22.5228, 113.9352));
        mPresets.add(new PlaceAdapter.PlaceInfo("杭州西湖断桥", "浙江省杭州市西湖区北山街", 30.2596, 120.1534));
        mPresets.add(new PlaceAdapter.PlaceInfo("成都天府广场", "四川省成都市青羊区人民南路一段", 30.6575, 104.0658));
    }

    private void filterPlaces(String query) {
        mFiltered.clear();
        if (query == null || query.trim().isEmpty()) {
            mFiltered.addAll(mPresets);
        } else {
            String lower = query.toLowerCase(java.util.Locale.US).trim();
            for (PlaceAdapter.PlaceInfo info : mPresets) {
                if (info.name.toLowerCase(java.util.Locale.US).contains(lower) || 
                    info.address.toLowerCase(java.util.Locale.US).contains(lower)) {
                    mFiltered.add(info);
                }
            }
        }
        mAdapter.setList(mFiltered);
    }
}
