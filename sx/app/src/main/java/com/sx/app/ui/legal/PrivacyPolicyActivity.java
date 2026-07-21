package com.sx.app.ui.legal;

import android.os.Bundle;
import android.view.MenuItem;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import com.google.android.material.appbar.MaterialToolbar;
import com.sx.app.R;

public class PrivacyPolicyActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_privacy_policy);

        MaterialToolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
            getSupportActionBar().setDisplayShowHomeEnabled(true);
        }

        TextView tvContent = findViewById(R.id.tv_privacy_content);
        tvContent.setText(getLegalContent());
    }

    @Override
    public boolean onOptionsItemSelected(@NonNull MenuItem item) {
        if (item.getItemId() == android.R.id.home) {
            finish();
            return true;
        }
        return super.onOptionsItemSelected(item);
    }

    private String getLegalContent() {
        return "【闪现 (sx) 用户协议与隐私政策】\n\n"
                + "版本发布日期：2026年7月21日\n"
                + "版本生效日期：2026年7月21日\n\n"
                + "欢迎使用「闪现 (sx)」软件。请您在开始使用前仔细阅读以下条款：\n\n"
                + "一、 用户协议\n"
                + "1. 服务说明：本软件提供多开隔离、环境参数测试及沙箱调试服务。\n"
                + "2. 使用规范：用户使用本软件须符合相关法律法规，不得用于任何违法、违规或侵犯他人合法权益之用途。\n"
                + "3. 免责声明：本软件为内测/RC版本，主要用于技术评估与功能验证，不承诺商业级稳定性及特定应用全面兼容。\n\n"
                + "二、 隐私政策\n"
                + "1. 信息收集与使用：本软件在本地运行沙箱环境，所配置的设备伪装参数（如伪装IMEI、MAC地址、虚拟定位等）仅在设备本地环境生效，不向第三方平台上传个人私密数据。\n"
                + "2. 权限说明：\n"
                + "   - 位置权限：用于测试沙箱内虚拟定位功能；\n"
                + "   - 存储与相机权限：用于虚拟预览图片加载及沙箱数据存储；\n"
                + "   - 网络权限：用于本地开发卡密激活校验与时钟防回拨同步。\n"
                + "3. 数据安全：我们采用严格的本地隔离防护机制，保护您的本地配置信息安全。\n\n"
                + "三、 软件属性说明\n"
                + "本版本为功能 RC 内测基线版本，仅供技术验证使用。如对条款有疑问，请联系系统管理员。";
    }
}
