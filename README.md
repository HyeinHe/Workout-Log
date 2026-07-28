# 健身记录 Workout Log

一个带 AI 分析的健身记录 Web 应用。记录训练动作、追踪个人记录、查看重量趋势，AI 自动生成训练总结和建议。

## 功能

- 记录训练：动作、组数、次数、重量（支持每组不同重量）
- AI 训练总结：DeepSeek API 自动分析并给出改进建议
- 训练日记：简洁查看每日训练，可随时补充感受
- 完整记录：查看历史详情，支持在线编辑和删除
- 数据分析：个人记录（PR）、重量趋势图、体重趋势图
- 动作记忆：常用动作自动保存，下次直接选择
- 多人使用：注册登录系统，数据独立存储
- 管理员面板：用户管理、重置密码、开关注册

## 技术栈

- **前端/后端**：Python + Streamlit
- **数据库**：Supabase（PostgreSQL）
- **AI 接口**：DeepSeek API
- **部署**：Streamlit Cloud

## 使用

1. 打开链接注册账号
2. 记录每日训练
3. AI 自动生成总结
4. 追踪力量增长趋势

## 本地运行

```bash
pip install streamlit requests supabase
streamlit run 健身记录_v20.py
```

需要在 `.streamlit/secrets.toml` 中配置：

```toml
SUPABASE_URL = "your_supabase_url"
SUPABASE_KEY = "your_supabase_key"
API_KEY = "your_deepseek_key"
```
