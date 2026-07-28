import streamlit as st
import requests, hashlib
from datetime import date
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
sb = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_USER = "HyeinHe"

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def fmt_type(t): return ", ".join(t) if isinstance(t, list) else t

st.set_page_config(page_title="健身记录", page_icon=":material/fitness_center:", layout="centered")
API_KEY = st.secrets["API_KEY"]

if "user" not in st.session_state: st.session_state.user = None

if not st.session_state.user:
    params=st.query_params
    if "user" in params:
        ex=sb.table("users").select("username").eq("username",params["user"]).execute()
        if ex.data: st.session_state.user=params["user"];st.rerun()
    st.title("健身记录")
    auth=st.radio("",["登录","注册"],horizontal=True)
    if auth=="登录":
        u=st.text_input("用户名",key="lu");p=st.text_input("密码",type="password",key="lp")
        if st.button("登录",use_container_width=True):
            r=sb.table("users").select("*").eq("username",u).eq("password",hash_pw(p)).execute()
            if r.data:
                st.session_state.user=u;st.query_params["user"]=u;st.rerun()
            else: st.error("用户名或密码错误")
    else:
        reg=sb.table("settings").select("value").eq("key","allow_reg").execute().data
        if reg and reg[0]["value"]=="false": st.warning("暂停注册，请联系管理员")
        else:
            u=st.text_input("用户名",key="ru");p=st.text_input("密码",type="password",key="rp")
            if st.button("注册",use_container_width=True):
                if not u or not p:st.error("请填写完整")
                else:
                    try: sb.table("users").insert({"username":u,"password":hash_pw(p)}).execute();st.success("注册成功")
                    except: st.error("用户已存在")
    st.stop()

user=st.session_state.user
c1,c2=st.columns([3,1])
with c1:st.caption(f"当前用户：{user}")
with c2:
    if st.button("退出登录"):
        st.session_state.user=None;st.query_params.clear();st.rerun()

labels=["记录训练","训练日记","完整记录","数据分析"]
labels.append("管理" if user==ADMIN_USER else "关于")
t1,t2,t3,t4,t5=st.tabs(labels)

with t1:
    st.title("今日健身记录")
    cd,cw=st.columns(2)
    with cd:rd=st.date_input("日期",value=date.today(),key="rd")
    with cw:bw=st.number_input("体重kg",0.0,200.0,0.0,0.5,key="bw")
    types=st.multiselect("部位",["胸","背","腿","肩","手臂","腹","有氧"],default=["胸"])
    edata=[];etext=[]
    num=st.number_input("几个动作",1,10,3,key="num")
    saved=[e["name"] for e in sb.table("user_exercises").select("name").eq("username",user).order("name").execute().data]
    for i in range(int(num)):
        st.markdown(f"**动作{i+1}**")
        choice=st.selectbox("选择或输入",["(新动作)"]+saved,key=f"sel_{i}")
        nm=st.text_input("新动作名称",key=f"nm_{i}") if choice=="(新动作)" else choice
        ca,cb=st.columns(2)
        with ca:se=st.number_input("组数",1,10,4,key=f"st_{i}")
        with cb:rp=st.number_input("次数",1,30,10,key=f"rp_{i}")
        cc,cd2=st.columns(2)
        with cc:wt=st.number_input("kg",0,300,0,5,key=f"wt_{i}")
        with cd2:mu=st.checkbox("不同重量",key=f"mu_{i}")
        if mu:
            sl=[]
            for s in range(int(se)):
                a1,a2,a3=st.columns([2,2,2])
                with a1:st.write(f"第{s+1}组")
                with a2:r=st.number_input("次",1,50,rp,key=f"mr_{i}_{s}")
                with a3:w=st.number_input("kg",0,300,0,5,key=f"mw_{i}_{s}")
                sl.append({"reps":int(r),"weight":w})
            if nm:
                txt="\n  ".join([f"{x['reps']}次x{'自重' if x['weight']==0 else str(x['weight'])+'kg'}" for x in sl])
                etext.append(f"{nm}：\n  {txt}");edata.append({"name":nm,"sets":sl})
        else:
            if nm:
                ws="自重" if wt==0 else f"{wt}kg"
                etext.append(f"{nm}：{int(se)}组x{int(rp)}次，{ws}")
                edata.append({"name":nm,"sets":[{"reps":int(rp),"weight":wt} for _ in range(int(se))]})
        st.divider()
    feel=st.text_area("日记",height=80,key="feel")
    if st.button("保存",use_container_width=True):
        if not edata:st.warning("至少填一个动作")
        else:
            log_text="训练部位："+fmt_type(types)+"\n"
            if etext:log_text+="\n动作：\n"+"\n".join(etext)
            if feel:log_text+="\n\n日记："+feel
            prompt="""你是一个资深健身教练，以下是我今天的训练记录：\n"""+log_text+"\n请总结：\n1.训练亮点\n2.容量/负重有无问题\n3.针对性改进建议\n语气专业简洁，聚焦实操，不要无脑吹捧。"
            with st.spinner("AI分析中..."):
                resp=requests.post("https://api.deepseek.com/v1/chat/completions",
                    headers={"Authorization":"Bearer "+API_KEY,"Content-Type":"application/json"},
                    json={"model":"deepseek-v4-pro","messages":[{"role":"user","content":prompt}]})
                result=resp.json()
                if "choices" not in result:st.error("API错误")
                else:
                    sm=result["choices"][0]["message"]["content"]
                    sb.table("records").insert({"username":user,"date":str(rd),"body_weight":bw,"type":fmt_type(types),"feeling":feel,"summary":sm}).execute()
                    rid=sb.table("records").select("id").eq("username",user).order("id",desc=True).limit(1).execute().data[0]["id"]
                    for ex in edata:
                        er=sb.table("exercises").insert({"record_id":rid,"name":ex["name"]}).execute()
                        eid=er.data[0]["id"]
                        for s in ex["sets"]:sb.table("sets").insert({"exercise_id":eid,"weight":s["weight"],"reps":s["reps"]}).execute()
                        try: sb.table("user_exercises").insert({"username":user,"name":ex["name"]}).execute()
                        except: pass
                    st.success(f"{rd} 已保存");st.markdown(sm)

with t2:
    st.title("训练日记")
    recs=sb.table("records").select("*").eq("username",user).order("date",desc=True).order("id",desc=True).execute().data
    if not recs:st.info("暂无记录")
    else:
        for r in recs:
            exs=sb.table("exercises").select("*").eq("record_id",r["id"]).execute().data
            bw=f" | 体重 {r['body_weight']}kg" if r["body_weight"]>0 else ""
            st.markdown(f"**{r['date']}**{bw}")
            for ex in exs:
                ss=sb.table("sets").select("*").eq("exercise_id",ex["id"]).execute().data
                st.markdown(f"**{ex['name']}**")
                for s in ss:st.markdown(f"  {s['reps']}次x{'自重' if s['weight']==0 else str(s['weight'])+'kg'}")
            sk=f"sk_{r['id']}"
            if r["feeling"]:
                with st.expander("感受"):st.write(r["feeling"])
            if st.button("编辑日记",key=f"fe_{r['id']}"):
                st.session_state[sk]=True
            if st.session_state.get(sk,False):
                nf=st.text_area("",value=r.get("feeling",""),key=f"nf_{r['id']}")
                if st.button("保存",key=f"sv_{r['id']}"):
                    sb.table("records").update({"feeling":nf}).eq("id",r["id"]).execute()
                    st.session_state[sk]=False;st.rerun()
            st.divider()

with t3:
    st.title("完整记录")
    recs=sb.table("records").select("*").eq("username",user).order("date",desc=True).order("id",desc=True).execute().data
    for idx,r in enumerate(recs):
        bw=f" | 体重 {r['body_weight']}kg" if r["body_weight"]>0 else ""
        with st.expander(f"{r['date']}{bw}"):
            exs=sb.table("exercises").select("*").eq("record_id",r["id"]).execute().data
            for ex in exs:
                ss=sb.table("sets").select("*").eq("exercise_id",ex["id"]).execute().data
                txt=" | ".join([f"{s['reps']}次x{s['weight']}kg" if s["weight"]>0 else f"{s['reps']}次x自重" for s in ss])
                st.write(f"**{ex['name']}**：{txt}")
                for s in ss:
                    ca,cb,cc=st.columns([2,2,1])
                    with ca:nw=st.number_input("kg",0.0,300.0,float(s["weight"]),2.5,key=f"ew_{s['id']}",label_visibility="collapsed")
                    with cb:nr=st.number_input("次",1,50,int(s["reps"]),key=f"er_{s['id']}",label_visibility="collapsed")
                    with cc:
                        if st.button("OK",key=f"sv_{s['id']}"):
                            sb.table("sets").update({"weight":nw,"reps":int(nr)}).eq("id",s["id"]).execute()
                            st.rerun()
            if r["feeling"]:st.write(f"日记：{r['feeling']}")
            if r["summary"]:st.markdown(f"**AI总结：**\n{r['summary']}")
            if st.button("删除",key=f"del_{idx}"):
                exs2=sb.table("exercises").select("id").eq("record_id",r["id"]).execute().data
                for ex in exs2:sb.table("sets").delete().eq("exercise_id",ex["id"]).execute()
                sb.table("exercises").delete().eq("record_id",r["id"]).execute()
                sb.table("records").delete().eq("id",r["id"]).execute();st.rerun()

with t4:
    st.title("数据分析")
    recs=sb.table("records").select("*").eq("username",user).order("date").execute().data
    prs={}
    for r in recs:
        exs=sb.table("exercises").select("*").eq("record_id",r["id"]).execute().data
        for ex in exs:
            ss=sb.table("sets").select("*").eq("exercise_id",ex["id"]).gt("weight",0).order("weight",desc=True).limit(1).execute().data
            if ss and (ex["name"] not in prs or ss[0]["weight"]>prs[ex["name"]]["weight"]):
                prs[ex["name"]]={"weight":ss[0]["weight"],"reps":ss[0]["reps"],"date":r["date"]}
    if prs:
        st.subheader("个人记录")
        for n,i in sorted(prs.items(),key=lambda x:x[1]["weight"],reverse=True):st.markdown(f"**{n}**：{i['weight']}kg x {i['reps']}次（{i['date']}）")
    ct=st.radio("趋势",["重量","体重"],horizontal=True)
    if ct=="重量":
        rows=[]
        for r in recs:
            exs=sb.table("exercises").select("*").eq("record_id",r["id"]).execute().data
            for ex in exs:
                ss=sb.table("sets").select("*").eq("exercise_id",ex["id"]).gt("weight",0).execute().data
                for s in ss:rows.append({"date":r["date"],"动作":ex["name"],"重量":s["weight"]})
        if rows:
            import pandas as pd;df=pd.DataFrame(rows)
            sel=st.selectbox("动作",df["动作"].unique())
            ex=df[df["动作"]==sel].copy();ex["date"]=pd.to_datetime(ex["date"]);ex=ex.sort_values("date")
            st.line_chart(ex.set_index("date")[["重量"]])
    else:
        rows=[{"date":r["date"],"体重":r["body_weight"]} for r in recs if r["body_weight"]>0]
        if rows:
            import pandas as pd;df=pd.DataFrame(rows)
            df["date"]=pd.to_datetime(df["date"]);df=df.sort_values("date")
            st.line_chart(df.set_index("date")[["体重"]])

with t5:
    if user==ADMIN_USER:
        st.title("管理面板")
        reg_v=sb.table("settings").select("value").eq("key","allow_reg").execute().data
        cur=reg_v[0]["value"]=="true" if reg_v else True
        reg=st.checkbox("允许新用户注册",value=cur)
        if reg!=cur:sb.table("settings").upsert({"key":"allow_reg","value":"true" if reg else "false"}).execute();st.rerun()
        st.divider()
        users=sb.table("users").select("username").execute().data
        st.write(f"共 {len(users)} 个用户")
        for uu in users:
            n=uu["username"]
            cnt=sb.table("records").select("id",count="exact").eq("username",n).execute().count
            st.write(f"**{n}**"+("（管理员）" if n==ADMIN_USER else "")+f" - {cnt}条记录")
            if n!=ADMIN_USER:
                ca,cb=st.columns([2,1])
                with ca:
                    with st.expander(f"重置{n}的密码"):
                        np=st.text_input("新密码",type="password",key=f"rp_{n}")
                        if st.button("确认",key=f"cr_{n}"):
                            if np:sb.table("users").update({"password":hash_pw(np)}).eq("username",n).execute();st.success("已重置")
                with cb:
                    if st.button("删除用户",key=f"du_{n}"):
                        rids=[r_id["id"] for r_id in sb.table("records").select("id").eq("username",n).execute().data]
                        for rid2 in rids:
                            exs2=sb.table("exercises").select("id").eq("record_id",rid2).execute().data
                            for ex2 in exs2:sb.table("sets").delete().eq("exercise_id",ex2["id"]).execute()
                            sb.table("exercises").delete().eq("record_id",rid2).execute()
                        sb.table("records").delete().eq("username",n).execute()
                        sb.table("user_exercises").delete().eq("username",n).execute()
                        sb.table("users").delete().eq("username",n).execute();st.rerun()
        st.divider()
        st.subheader("发布公告")
        ann=sb.table("settings").select("value").eq("key","announcement").execute().data
        cur_ann=ann[0]["value"] if ann else ""
        new_ann=st.text_area("公告内容（所有用户将在「关于」页面看到）",value=cur_ann,height=100)
        if st.button("发布公告"):
            ex_ann=sb.table("settings").select("*").eq("key","announcement").execute().data
if ex_ann:sb.table("settings").update({"value":new_ann}).eq("key","announcement").execute()
else:sb.table("settings").insert({"key":"announcement","value":new_ann}).execute()
st.success("公告已发布")
else:
        st.title("关于")
        ann=sb.table("settings").select("value").eq("key","announcement").execute().data
        if ann and ann[0]["value"]:
            st.info(ann[0]["value"])
            st.divider()
        st.write("健身记录 v21")
        st.divider()
        st.subheader("修改密码")
        op=st.text_input("当前密码",type="password",key="op")
        np=st.text_input("新密码",type="password",key="np")
        if st.button("修改密码",use_container_width=True):
            if not op or not np:st.error("请填写完整")
            else:
                ck=sb.table("users").select("*").eq("username",user).eq("password",hash_pw(op)).execute()
                if not ck.data:st.error("当前密码错误")
                else:sb.table("users").update({"password":hash_pw(np)}).eq("username",user).execute();st.success("已修改")
