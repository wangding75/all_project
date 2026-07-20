package com.sx.app.ui.sandbox;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import com.sx.app.R;
import com.sx.app.sandbox.HostAppInfo;
import java.util.ArrayList;
import java.util.List;

public class HostAppAdapter extends RecyclerView.Adapter<HostAppAdapter.ViewHolder> {

    private final Context mContext;
    private final List<HostAppInfo> mData = new ArrayList<>();
    private OnItemClickListener mListener;

    public interface OnItemClickListener {
        void onItemClick(HostAppInfo info);
    }

    public HostAppAdapter(Context context, OnItemClickListener listener) {
        mContext = context;
        mListener = listener;
    }

    public void setList(List<HostAppInfo> list) {
        mData.clear();
        if (list != null) {
            mData.addAll(list);
        }
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(mContext).inflate(R.layout.item_sandbox_app, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        HostAppInfo info = mData.get(position);
        holder.tvName.setText(info.label);
        holder.tvPkg.setText(info.packageName);
        holder.tvUser.setVisibility(View.GONE); // Hide user index for host apps
        holder.ivIcon.setImageDrawable(info.icon);

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
        ImageView ivIcon;
        TextView tvName;
        TextView tvPkg;
        TextView tvUser;

        public ViewHolder(@NonNull View itemView) {
            super(itemView);
            ivIcon = itemView.findViewById(R.id.iv_icon);
            tvName = itemView.findViewById(R.id.tv_name);
            tvPkg = itemView.findViewById(R.id.tv_pkg);
            tvUser = itemView.findViewById(R.id.tv_user);
        }
    }
}
