package com.sx.app.ui.location;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import com.sx.app.R;
import java.util.ArrayList;
import java.util.List;

public class PlaceAdapter extends RecyclerView.Adapter<PlaceAdapter.ViewHolder> {

    public static class PlaceInfo {
        public String name;
        public String address;
        public double latitude;
        public double longitude;

        public PlaceInfo(String name, String address, double latitude, double longitude) {
            this.name = name;
            this.address = address;
            this.latitude = latitude;
            this.longitude = longitude;
        }
    }

    private final Context mContext;
    private final List<PlaceInfo> mData = new ArrayList<>();
    private OnItemClickListener mListener;

    public interface OnItemClickListener {
        void onItemClick(PlaceInfo info);
    }

    public PlaceAdapter(Context context, OnItemClickListener listener) {
        mContext = context;
        mListener = listener;
    }

    public void setList(List<PlaceInfo> list) {
        mData.clear();
        if (list != null) {
            mData.addAll(list);
        }
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(mContext).inflate(R.layout.item_place, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        PlaceInfo info = mData.get(position);
        holder.tvName.setText(info.name);
        holder.tvAddr.setText(info.address + " (" + info.latitude + ", " + info.longitude + ")");

        holder.itemView.setOnClickListener(v -> {
            if (mListener != null) {
                mListener.onItemClick(info);
            }
        });
    }

    @Override
    public int getItemCount() {
        return mData.size();
    }

    static class ViewHolder extends RecyclerView.ViewHolder {
        TextView tvName;
        TextView tvAddr;

        public ViewHolder(@NonNull View itemView) {
            super(itemView);
            tvName = itemView.findViewById(R.id.tv_name);
            tvAddr = itemView.findViewById(R.id.tv_addr);
        }
    }
}
