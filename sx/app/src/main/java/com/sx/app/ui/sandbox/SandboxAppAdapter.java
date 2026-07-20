package com.sx.app.ui.sandbox;

import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.drawable.Drawable;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import com.sx.app.R;
import com.sx.app.data.SandboxAppInfo;
import java.util.ArrayList;
import java.util.List;

public class SandboxAppAdapter extends RecyclerView.Adapter<SandboxAppAdapter.ViewHolder> {

    private final Context mContext;
    private final List<SandboxAppInfo> mData = new ArrayList<>();

    public SandboxAppAdapter(Context context) {
        mContext = context;
    }

    public void setList(List<SandboxAppInfo> list) {
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
        SandboxAppInfo info = mData.get(position);
        holder.tvName.setText(info.label);
        holder.tvPkg.setText(info.packageName);
        holder.tvUser.setText("分身 #" + (info.userId + 1));
        
        // Hide/Show userId tag
        if (info.userId == 0) {
            holder.tvUser.setVisibility(View.GONE);
        } else {
            holder.tvUser.setVisibility(View.VISIBLE);
        }

        PackageManager pm = mContext.getPackageManager();
        try {
            Drawable icon = pm.getApplicationIcon(info.packageName);
            holder.ivIcon.setImageDrawable(icon);
        } catch (PackageManager.NameNotFoundException e) {
            holder.ivIcon.setImageResource(R.drawable.ic_launcher);
        }

        holder.itemView.setOnClickListener(v -> {
            Intent intent = new Intent(mContext, AppDetailActivity.class);
            intent.putExtra("package_name", info.packageName);
            intent.putExtra("user_id", info.userId);
            mContext.startActivity(intent);
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
