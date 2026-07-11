"""Build the HCAI Atlas keyword graph from publication abstracts."""
from __future__ import annotations
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = json.loads((ROOT / "outputs/publication_abstracts_cache.json").read_text(encoding="utf-8"))

DOMAINS = {
    "cognition": ("Human Cognition", "#8b7bff", [
        ("Visual Attention", ["visual attention", "spatial attention", "feature-based attention"]),
        ("Cognitive Modeling", ["cognitive model", "cognitive process", "cognitively inspired"]),
        ("Embodied Cognition", ["embodied cognition", "embodied reference"]),
        ("Expertise", ["expertise", "expert drivers", "expert and novice"]),
        ("Decision Making", ["decision-making", "decision making"]),
        ("Emotion Regulation", ["emotion regulation", "emotional strategies"]),
        ("Mental Models", ["mental model", "problem structure"]),
        ("Neural Mechanisms", ["neural mechanism", "neural pathway", "brain activity"]),
        ("Perception", ["perception", "perceptual", "sensory"]),
        ("Human Behavior", ["human behavior", "behavioral data", "lived experiences"]),
    ]),
    "ai": ("AI & Agents", "#39a7ff", [
        ("Large Language Models", ["large language model", "llm", "language models"]),
        ("Generative Agents", ["generative agent", "driver agent", "agent framework"]),
        ("Human-State Modeling", ["human state", "user state", "client profile"]),
        ("Retrieval-Augmented Generation", ["retrieval-augmented", "rag", "knowledge retrieval"]),
        ("Vision-Language Models", ["vision-language", "vision language", "vlm"]),
        ("Reinforcement Learning", ["reinforcement learning", "imitation reinforcement"]),
        ("World Models", ["world model", "simulation framework"]),
        ("Trajectory Prediction", ["trajectory prediction", "motion prediction"]),
        ("Algorithmic Attention", ["algorithmic attention", "attention mechanism"]),
        ("End-to-End Learning", ["end-to-end", "end2end"]),
    ]),
    "interaction": ("Human–AI Interaction", "#23e0c1", [
        ("Human–AI Collaboration", ["human-ai collaboration", "human-agent collaboration", "collaborative dynamics"]),
        ("Human–Robot Interaction", ["human-robot", "robot interaction", "guide robots"]),
        ("Co-Design", ["co-design", "participatory design"]),
        ("Conversational Agents", ["conversational agent", "ai counselor", "dialogue interaction"]),
        ("Proactive Interaction", ["proactive", "mixed-initiative"]),
        ("Telepresence", ["telepresence", "remote collaborative"]),
        ("Multimodal Interaction", ["multimodal interaction", "multi-modal interaction"]),
        ("Tangible Interaction", ["tangible", "tactile interaction"]),
        ("Immersive Interaction", ["immersive", "mixed reality", "virtual reality"]),
        ("User Experience", ["user experience", "usability"]),
    ]),
    "methods": ("Human Research Methods", "#65df72", [
        ("Eye Tracking", ["eye tracking", "eye-tracking", "fixation data"]),
        ("EEG", ["eeg", "electroencephalography"]),
        ("Physiological Sensing", ["physiological", "heart rate", "electrodermal"]),
        ("Qualitative Interviews", ["semi-structured interviews", "qualitative study", "interviews"]),
        ("Controlled Studies", ["controlled study", "controlled experiment", "user study"]),
        ("Field Studies", ["field study", "field observations", "real-world"]),
        ("Behavioral Sensing", ["behavioral data", "interaction traces"]),
        ("Discourse Analysis", ["discourse coding", "sequential analysis"]),
        ("Simulation", ["simulation", "simulator"]),
        ("Dataset Construction", ["dataset", "data collection"]),
    ]),
    "evaluation": ("Evaluation", "#f6d365", [
        ("Human-Centered Benchmarking", ["benchmark", "evaluation framework"]),
        ("Safety Evaluation", ["safety evaluation", "safety-critical", "pedestrian safety"]),
        ("Driving Intelligence", ["driving intelligence", "driving performance"]),
        ("Learning Outcomes", ["learning outcomes", "learning performance"]),
        ("Engagement", ["engagement", "client engagement"]),
        ("Trust & Reliance", ["trust", "reliance"]),
        ("Accessibility Evaluation", ["accessibility", "visually impaired", "blindness and low vision"]),
        ("Longitudinal Effects", ["long-term", "longitudinal"]),
        ("Human–AI Resemblance", ["human-ai resemblance", "human-like"]),
        ("Ecological Validity", ["naturalistic", "authentic classroom", "real-world"]),
    ]),
    "education": ("AI & Learning", "#ff9c55", [
        ("AI Mentoring", ["ai mentor", "mentoring students", "mentor configurations"]),
        ("Collaborative Learning", ["collaborative learning", "group-level reasoning"]),
        ("Creative Problem Solving", ["creative problem-solving", "creative problem solving"]),
        ("Project-Based Learning", ["project-based learning", "pbl"]),
        ("Child-Centric AI", ["child-centric ai", "children's learning", "school students"]),
        ("Teacher Orchestration", ["teacher orchestration", "teacher intervention"]),
        ("Social Learning", ["social learning", "social and collaborative skills"]),
        ("Intelligent Tutoring", ["intelligent tutoring", "learning support"]),
    ]),
    "wellbeing": ("Health & Well-being", "#ff5d73", [
        ("Mental Health", ["mental health", "psychological counseling"]),
        ("AI Counseling", ["ai counselor", "counselor-inspired", "counseling agent"]),
        ("Music Therapy", ["music therapy", "emotion-focused therapy"]),
        ("Autism Support", ["autistic children", "autism"]),
        ("Emotional Support", ["emotional support", "companionship"]),
        ("Well-being", ["well-being", "wellbeing"]),
        ("Expressive Arts Therapy", ["expressive arts", "arts therapy"]),
        ("Assistive Technology", ["assistive technology", "accessibility"]),
    ]),
    "mobility": ("Mobility & Embodied AI", "#f071d6", [
        ("Autonomous Driving", ["autonomous driving", "automated vehicle"]),
        ("Driving Cognition", ["driving cognition", "driver decision", "driving expertise"]),
        ("Hazard Perception", ["hazard", "hazardous driving", "risk perception"]),
        ("Embodied AI", ["embodied ai", "embodied intelligence"]),
        ("Navigation", ["navigation", "route modeling"]),
        ("Pedestrian Interaction", ["pedestrian", "traffic settings"]),
        ("Guide Robots", ["guide robot", "guide dogs", "quadruped"]),
        ("Closed-Loop Simulation", ["closed-loop", "interactive simulator"]),
        ("Driving Style", ["driving style", "driver behavior"]),
        ("Long-Tail Scenarios", ["long-tail", "unstructured environments"]),
    ]),
}

# Stable semantic vertical axis used by the Atlas (0 = top, 5 = bottom).
# Domain defaults keep the map legible; keyword overrides place hybrid topics
# according to what they represent rather than only by their color/domain.
DOMAIN_LEVELS = {
    "ai": 0, "mobility": 1, "interaction": 2, "education": 2,
    "wellbeing": 2, "evaluation": 3, "methods": 4, "cognition": 5,
}
LEVEL_OVERRIDES = {
    "Human-State Modeling": 0, "World Models": 0, "Trajectory Prediction": 0,
    "Algorithmic Attention": 0, "End-to-End Learning": 0,
    "Embodied AI": 2, "Autonomous Driving": 2, "Closed-Loop Simulation": 2,
    "Simulation": 3, "Dataset Construction": 3, "Behavioral Sensing": 3,
}

def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    head = text.split("---", 2)[1] if text.startswith("---") else ""
    out = {}
    for key in ("title", "year", "venue", "authors", "permalink", "link"):
        m = re.search(rf"(?m)^{key}:\s*[\"']?(.*?)[\"']?\s*$", head)
        if m: out[key] = m.group(1).strip().strip('"')
    return out

papers = []
for rel, item in CACHE.items():
    abstract = (item.get("abstract") or "").strip()
    path = ROOT / rel
    if not abstract or not path.exists(): continue
    meta = frontmatter(path)
    papers.append({
        "id": path.stem, "title": meta.get("title", item.get("title", "")),
        "year": int(meta.get("year") or item.get("year") or 0), "venue": meta.get("venue", ""),
        "authors": meta.get("authors", ""), "url": meta.get("permalink", "/publications/"),
        "external": meta.get("link", item.get("url", "")), "abstract": abstract,
    })

nodes = []
for domain, (title, color, terms) in DOMAINS.items():
    for order, (label, aliases) in enumerate(terms):
        ids=[]
        for p in papers:
            hay=(p["title"]+" "+p["abstract"]).lower()
            if any(a.lower() in hay for a in aliases): ids.append(p["id"])
        nodes.append({"id": re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-"), "name":label,
                      "domain":domain, "level":LEVEL_OVERRIDES.get(label, DOMAIN_LEVELS[domain]),
                      "paperIds":ids, "aliases":aliases})

edges=[]
for domain in DOMAINS:
    group=[n for n in nodes if n["domain"]==domain]
    for a,b in zip(group,group[1:]): edges.append({"source":a["id"],"target":b["id"]})
for i,a in enumerate(nodes):
    aset=set(a["paperIds"])
    if not aset: continue
    best=None; score=0
    for b in nodes[i+1:]:
        if a["domain"]==b["domain"]: continue
        overlap=len(aset & set(b["paperIds"]))
        if overlap>score: best,score=b,overlap
    if best and score>=2: edges.append({"source":a["id"],"target":best["id"]})

payload={"domains":[{"id":k,"name":v[0],"color":v[1]} for k,v in DOMAINS.items()],
         "nodes":nodes,"edges":edges,"papers":sorted(papers,key=lambda p:(p["year"],p["title"]),reverse=True)}
out=ROOT/"assets/data/hcai-atlas.json"; out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(payload,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
print(f"wrote {len(nodes)} nodes, {len(edges)} edges, {len(papers)} papers -> {out}")
