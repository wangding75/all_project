package com.loc.va.ui.activity;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.EditText;
import android.widget.ListView;

import java.util.ArrayList;
import java.util.List;

/**
 * 百度地图位置搜索/选点页
 * 功能：
 *   1. 在百度地图上点击选择虚拟定位坐标
 *   2. 搜索地点名称（关键字搜索）
 *   3. 跨城市搜索（格式：城市名@关键词）
 *   4. 历史位置记录
 *   5. 确认选择坐标，返回给 LocationSettingsActivity
 *
 * 原始类名：com.loc.va.ui.activity.LocationSearchActivity
 * 标题：地点选择（activity_choose_location）
 */
public class LocationSearchActivity extends Activity {

    private EditText etSearch;
    private View mapView;    // 百度地图 MapView
    private ListView lvSearchResult;
    private View btnConfirm;
    private View tvSelectedLoc;

    // 当前选中的坐标
    private double selectedLat = 0.0;
    private double selectedLng = 0.0;
    private String selectedAddress = "";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // setContentView(R.layout.activity_location_search);

        initViews();
        initMap();
        setupSearchListener();
    }

    private void initViews() {
        // etSearch = findViewById(R.id.et_search);
        // mapView = findViewById(R.id.map_view);
        // lvSearchResult = findViewById(R.id.lv_search_result);
        // btnConfirm = findViewById(R.id.btn_confirm);
        // tvSelectedLoc = findViewById(R.id.tv_selected_loc);
    }

    /**
     * 初始化百度地图
     */
    private void initMap() {
        // BaiduMap baiduMap = ((MapView) mapView).getMap();

        // 设置地图点击监听（选点）
        // baiduMap.setOnMapClickListener(latLng -> {
        //     selectedLat = latLng.latitude;
        //     selectedLng = latLng.longitude;
        //     updateSelectedMarker(latLng);
        //     reverseGeocode(latLng);  // 逆地理编码获取地址名称
        //     updateSelectionDisplay();
        // });
    }

    /**
     * 设置搜索框输入监听
     * 提示：搜索非当前城市区域，请用:"城市名@关键词"
     */
    private void setupSearchListener() {
        // etSearch.addTextChangedListener(new TextWatcher() {
        //     @Override
        //     public void onTextChanged(CharSequence s, int start, int before, int count) {
        //         if (s.length() > 1) {
        //             performSearch(s.toString());
        //         }
        //     }
        // });
    }

    /**
     * 执行地点搜索
     * 格式支持：
     *   - "关键词"：搜索当前城市
     *   - "城市名@关键词"：搜索指定城市
     */
    private void performSearch(String keyword) {
        String city = "全国";
        String searchKeyword = keyword;

        if (keyword.contains("@")) {
            String[] parts = keyword.split("@");
            if (parts.length == 2) {
                city = parts[0];
                searchKeyword = parts[1];
            }
        }

        // 调用百度 POI 搜索 API
        // PoiSearch.SearchOption option = new PoiCitySearchOption()
        //     .city(city)
        //     .keyword(searchKeyword);
    }

    /**
     * 更新选中位置的显示
     * 格式：坐标：纬度 X.XXXXXXXX; 经度 X.XXXXXXXX
     */
    private void updateSelectionDisplay() {
        String coordText = String.format("坐标：纬度 %.8f; 经度 %.8f", selectedLat, selectedLng);
        // tvSelectedLoc.setText(coordText);
    }

    /**
     * 确认选择位置，返回坐标给调用方
     */
    private void confirmSelection() {
        if (selectedLat == 0.0 && selectedLng == 0.0) {
            // "还未选择模拟位置"
            return;
        }

        Intent result = new Intent();
        result.putExtra("lat", selectedLat);
        result.putExtra("lng", selectedLng);
        result.putExtra("address", selectedAddress);
        setResult(RESULT_OK, result);
        finish();
    }

    @Override
    protected void onResume() {
        super.onResume();
        // mapView.onResume();
    }

    @Override
    protected void onPause() {
        super.onPause();
        // mapView.onPause();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        // mapView.onDestroy();
    }
}
