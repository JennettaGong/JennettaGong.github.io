(function () {
  const domains = {
    'Human Cognition':'人类认知','AI & Agents':'AI 与智能体','Human–AI Interaction':'人机 AI 交互',
    'Human Research Methods':'人类研究方法','Evaluation':'评估','AI & Learning':'AI 与学习',
    'Health & Well-being':'健康与福祉','Mobility & Embodied AI':'移动与具身智能'
  };
  const nodes = {
    'Visual Attention':'视觉注意','Cognitive Modeling':'认知建模','Embodied Cognition':'具身认知','Expertise':'专业技能','Decision Making':'决策','Emotion Regulation':'情绪调节','Mental Models':'心智模型','Neural Mechanisms':'神经机制','Perception':'知觉','Human Behavior':'人类行为',
    'Large Language Models':'大语言模型','Generative Agents':'生成式智能体','Human-State Modeling':'人类状态建模','Retrieval-Augmented Generation':'检索增强生成','Vision-Language Models':'视觉语言模型','Reinforcement Learning':'强化学习','World Models':'世界模型','Trajectory Prediction':'轨迹预测','Algorithmic Attention':'算法注意力','End-to-End Learning':'端到端学习',
    'Human–AI Collaboration':'人机 AI 协作','Human–Robot Interaction':'人机交互','Co-Design':'共同设计','Conversational Agents':'对话智能体','Proactive Interaction':'主动交互','Telepresence':'远程临场','Multimodal Interaction':'多模态交互','Tangible Interaction':'实物交互','Immersive Interaction':'沉浸式交互','User Experience':'用户体验',
    'Eye Tracking':'眼动追踪','EEG':'脑电','Physiological Sensing':'生理感知','Qualitative Interviews':'定性访谈','Controlled Studies':'对照研究','Field Studies':'田野研究','Behavioral Sensing':'行为感知','Discourse Analysis':'话语分析','Simulation':'仿真','Dataset Construction':'数据集构建',
    'Human-Centered Benchmarking':'以人为中心的基准测试','Safety Evaluation':'安全评估','Driving Intelligence':'驾驶智能','Learning Outcomes':'学习成果','Engagement':'参与度','Trust & Reliance':'信任与依赖','Accessibility Evaluation':'无障碍评估','Longitudinal Effects':'长期影响','Human–AI Resemblance':'人与 AI 相似性','Ecological Validity':'生态效度',
    'AI Mentoring':'AI 导师','Collaborative Learning':'协作学习','Creative Problem Solving':'创造性问题解决','Project-Based Learning':'项目式学习','Child-Centric AI':'儿童中心 AI','Teacher Orchestration':'教师教学编排','Social Learning':'社会化学习','Intelligent Tutoring':'智能辅导',
    'Mental Health':'心理健康','AI Counseling':'AI 心理咨询','Music Therapy':'音乐治疗','Autism Support':'孤独症支持','Emotional Support':'情绪支持','Well-being':'福祉','Expressive Arts Therapy':'表达性艺术治疗','Assistive Technology':'辅助技术',
    'Autonomous Driving':'自动驾驶','Driving Cognition':'驾驶认知','Hazard Perception':'危险感知','Embodied AI':'具身智能','Navigation':'导航','Pedestrian Interaction':'行人交互','Guide Robots':'引导机器人','Closed-Loop Simulation':'闭环仿真','Driving Style':'驾驶风格','Long-Tail Scenarios':'长尾场景'
  };
  const reverse = Object.fromEntries(Object.entries(nodes).map(([en, zh]) => [zh, en]));
  const reverseDomains = Object.fromEntries(Object.entries(domains).map(([en, zh]) => [zh, en]));
  let scheduled = false, observer;

  function language() { return document.documentElement.dataset.lang || 'en'; }
  function translate(value, map, reverseMap, lang) {
    return lang === 'zh' ? (map[value] || value) : (reverseMap[value] || value);
  }
  function text(selector, en, zh, lang) {
    const el = document.querySelector(selector); if (el) el.textContent = lang === 'zh' ? zh : en;
  }
  function html(selector, en, zh, lang) {
    const el = document.querySelector(selector); if (el) el.innerHTML = lang === 'zh' ? zh : en;
  }
  function apply() {
    scheduled = false;
    if (observer) observer.disconnect();
    const lang = language();
    text('.loading','INITIALIZING KNOWLEDGE UNIVERSE…','正在初始化知识宇宙…',lang);
    text('.home span','BACK TO PERSONAL HOMEPAGE','返回个人主页',lang);
    text('.intro .kicker','RESEARCH IDEAS EXTRACTED FROM PUBLICATION ABSTRACTS','从论文摘要中提取的研究概念',lang);
    html('.intro h1','Explore the ideas<br>behind my<br><em>Human-Centered AI.</em>','探索我的<br><em>以人为中心的 AI</em><br>研究脉络。',lang);
    text('.intro>p:not(.kicker)','Every glowing node is a research keyword extracted from my papers. Select one to reveal the publications connected to that idea.','每个发光节点都是从论文中提取的研究关键词。点击节点，查看与该概念相关的论文。',lang);
    const spin = document.querySelector('#spin');
    if (spin) {
      const paused = /RESUME|继续/.test(spin.textContent);
      spin.textContent = paused ? (lang === 'zh' ? '▶ 继续旋转' : '▶ RESUME UNIVERSE') : (lang === 'zh' ? '◼ 暂停旋转' : '◼ PAUSE UNIVERSE');
    }
    text('.controls a','ALL PUBLICATIONS →','全部论文 →',lang);
    text('.legend>p','RESEARCH DOMAINS · CLICK TO FILTER','研究领域 · 点击筛选',lang);
    text('.hint','DRAG TO ORBIT · TAP A KEYWORD · OPEN ITS PAPERS','拖动旋转 · 点击关键词 · 查看相关论文',lang);
    const guide = [
      ['ALGORITHM OPTIMIZATION','AI models & algorithms','算法优化','AI 模型与算法'],
      ['INTELLIGENT SYSTEM DESIGN','systems & human–AI collaboration','智能系统设计','系统与人机 AI 协作'],
      ['HUMAN UNDERSTANDING','qualitative & quantitative','理解人','定性与定量研究'],
      ['COGNITIVE INSTRUMENTS','mind, behavior & neural evidence','认知工具','心智、行为与神经证据']
    ];
    document.querySelectorAll('.layer-guide span').forEach((el, i) => {
      if (!guide[i]) return; const g=guide[i]; el.childNodes[0].nodeValue=lang==='zh'?g[2]:g[0]; const b=el.querySelector('b'); if(b)b.textContent=lang==='zh'?g[3]:g[1];
    });
    document.querySelectorAll('#legend button span').forEach(el => { el.textContent=translate(el.textContent,domains,reverseDomains,lang); });
    const domainLabel=document.querySelector('.panel .domain-label');
    if(domainLabel){const raw=domainLabel.textContent.trim();const normal=Object.keys(domains).find(k=>k.toUpperCase()===raw)||Object.keys(reverseDomains).find(k=>k===raw)||raw;domainLabel.textContent=translate(normal,domains,reverseDomains,lang).toUpperCase();}
    const nodeTitle=document.querySelector('.panel h2'); if(nodeTitle)nodeTitle.textContent=translate(nodeTitle.textContent,nodes,reverse,lang);
    const aliases=document.querySelector('.panel .aliases'); if(aliases&&aliases.textContent)aliases.textContent=aliases.textContent.replace(/^ABSTRACT SIGNALS · |^摘要关键词 · /,lang==='zh'?'摘要关键词 · ':'ABSTRACT SIGNALS · ');
    const count=document.querySelector('.panel .paper-count'); if(count&&count.textContent){const n=count.textContent.match(/\d+/);if(n)count.textContent=lang==='zh'?`相关论文 ${n[0]} 篇`:`${n[0]} RELATED PUBLICATION${n[0]==='1'?'':'S'}`;}
    const empty=document.querySelector('.panel .empty'); if(empty)empty.textContent=lang==='zh'?'该概念已进入图谱，但目前没有摘要与它形成足够强的直接关联。':'This emerging concept is part of the map, but no abstract currently has a strong direct match.';
    const tipTitle=document.querySelector('.tooltip b'); if(tipTitle)tipTitle.textContent=translate(tipTitle.textContent,nodes,reverse,lang);
    const tipMeta=document.querySelector('.tooltip span'); if(tipMeta&&tipMeta.textContent){const m=tipMeta.textContent.match(/(\d+) papers · (.+)|(\d+) 篇论文 · (.+)/);if(m){const n=m[1]||m[3],d=m[2]||m[4];tipMeta.textContent=lang==='zh'?`${n} 篇论文 · ${translate(d,domains,reverseDomains,'zh')}`:`${n} papers · ${translate(d,domains,reverseDomains,'en')}`;}}
    const close=document.querySelector('.panel .close'); if(close)close.setAttribute('aria-label',lang==='zh'?'关闭':'Close');
    if (observer) observer.observe(document.body,{childList:true,subtree:true,characterData:true});
  }
  function schedule(){if(!scheduled){scheduled=true;setTimeout(apply,0);}}
  window.addEventListener('site-language-change',schedule);
  document.addEventListener('DOMContentLoaded',function(){observer=new MutationObserver(schedule);apply();});
})();
