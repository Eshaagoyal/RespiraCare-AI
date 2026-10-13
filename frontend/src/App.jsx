import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Home from './pages/Home';
import Chat from './pages/Chat';
import { 
  ShieldAlert, 
  HelpCircle, 
  Layers, 
  Cpu, 
  CheckCircle2, 
  FileText, 
  AlertTriangle, 
  BookOpen, 
  Activity, 
  Sparkles, 
  ArrowRight, 
  ShieldCheck, 
  Stethoscope, 
  HeartPulse, 
  Database, 
  Check,
  Wind,
  MessageSquare,
  Clock
} from 'lucide-react';

const HowItWorks = () => {
  const useCases = [
    {
      id: "triggers",
      badge: "Symptom & Triggers",
      title: "1. Symptom & Trigger Identification",
      desc: "Understand the subtle causes behind your breathing difficulties. Whether it is pollen, temperature drops, exercise, or indoor dust, RespiraCare AI helps you identify common triggers and recognize patterns like nighttime coughing.",
      icon: <Wind className="w-6 h-6 text-sky-600" />,
      accentBorder: "border-sky-200",
      accentBg: "bg-sky-50 text-sky-700",
      takeaway: "Pinpointing personal triggers helps prevent acute flare-ups before they begin.",
      sampleQueries: [
        "Why does my chest feel tight and wheezy after exercising in cold weather?",
        "I've been waking up with a persistent cough at night. What could cause this?",
        "How do seasonal allergens like pollen differ from indoor dust triggers?"
      ]
    },
    {
      id: "care",
      badge: "Inhalers & Daily Care",
      title: "2. Inhaler Technique & Self-Management",
      desc: "Receive clear, step-by-step guidance on proper inhaler usage—including the crucial distinction between daily steroid preventers and rapid-acting relievers. Learn how spacer devices improve drug absorption and how to follow an Asthma Action Plan.",
      icon: <Stethoscope className="w-6 h-6 text-emerald-600" />,
      accentBorder: "border-emerald-200",
      accentBg: "bg-emerald-50 text-emerald-700",
      takeaway: "Correct inhaler technique ensures medication reaches deep lung airways rather than just the throat.",
      sampleQueries: [
        "What is the difference between a reliever (blue) and a preventer inhaler?",
        "How do I correctly use and clean a spacer device?",
        "What should be included in a personal written Asthma Action Plan?"
      ]
    },
    {
      id: "emergency",
      badge: "Emergency & Clinical Safety",
      title: "3. Emergency Red-Flags & When to See a Doctor",
      desc: "Immediate detection of acute respiratory emergencies. If you report severe warning signs—such as blue lips, inability to finish sentences, or an inhaler failing to provide relief—the system instantly displays emergency steps and directs you to emergency medical care.",
      icon: <ShieldAlert className="w-6 h-6 text-red-600" />,
      accentBorder: "border-red-200",
      accentBg: "bg-red-50 text-red-700",
      takeaway: "Red-flag guardrails ensure critical symptoms are never downplayed or delayed.",
      sampleQueries: [
        "My inhaler isn't helping and I am struggling to breathe or speak.",
        "What are the telltale warning signs of a severe asthma attack?",
        "When is it safe to manage symptoms at home vs scheduling an urgent doctor visit?"
      ]
    }
  ];

  const quickSteps = [
    {
      step: "1",
      title: "Describe Your Concern",
      desc: "Type naturally in plain English or conversational phrasing. No complex medical terms needed."
    },
    {
      step: "2",
      title: "Smart Follow-Up Questions",
      desc: "If symptoms are vague, the assistant asks a targeted clarifying question instead of guessing."
    },
    {
      step: "3",
      title: "Guideline-Backed Advice",
      desc: "Receive clear explanations with verified source citations from GINA 2024 and NHS UK."
    }
  ];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12">
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto mb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold uppercase tracking-wider mb-4">
          <HeartPulse className="w-3.5 h-3.5 text-blue-600" />
          Everyday Clinical Support
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight mb-4">
          How RespiraCare AI Supports You
        </h1>
        <p className="text-base sm:text-lg text-slate-600 leading-relaxed">
          From everyday trigger management to correct inhaler techniques and urgent safety warnings, discover how RespiraCare AI provides clear, evidence-grounded answers.
        </p>
      </div>

      {/* Quick 3-Step Process Bar */}
      <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-slate-200 mb-12">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-6 text-center">
          How A Conversation Works In 3 Simple Steps
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {quickSteps.map((qs, i) => (
            <div key={i} className="flex gap-4 items-start">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 text-white font-bold text-sm flex items-center justify-center">
                {qs.step}
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900 mb-1">{qs.title}</h3>
                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">{qs.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Section: 3 Core Clinical Use Cases */}
      <div className="space-y-8 mb-12">
        {useCases.map((uc) => (
          <div 
            key={uc.id} 
            className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-slate-200 hover:shadow-md transition-shadow"
          >
            <div className="flex flex-col sm:flex-row sm:items-start gap-5 mb-5">
              <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-center">
                {uc.icon}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${uc.accentBg} ${uc.accentBorder}`}>
                    {uc.badge}
                  </span>
                </div>
                <h2 className="text-xl font-bold text-slate-900 mb-2">
                  {uc.title}
                </h2>
                <p className="text-slate-600 leading-relaxed text-sm sm:text-base mb-3">
                  {uc.desc}
                </p>
                <div className="text-xs sm:text-sm text-slate-500 italic bg-slate-50 border border-slate-100 rounded-lg px-3 py-2">
                  💡 <strong>Clinical Value:</strong> {uc.takeaway}
                </div>
              </div>
            </div>

            {/* Sample Prompts / Example Queries */}
            <div className="border-t border-slate-100 pt-4 mt-4">
              <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <MessageSquare className="w-3.5 h-3.5 text-blue-600" />
                Common Questions You Can Ask:
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                {uc.sampleQueries.map((q, idx) => (
                  <div 
                    key={idx}
                    className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 leading-relaxed flex items-start gap-2"
                  >
                    <span className="text-blue-500 font-bold">•</span>
                    <span>&ldquo;{q}&rdquo;</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* CTA Box */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-8 text-white text-center shadow-lg">
        <h3 className="text-2xl font-bold mb-2">Have An Asthma Question?</h3>
        <p className="text-blue-100 max-w-xl mx-auto text-sm sm:text-base mb-6">
          Explore personalized trigger guidance, inhaler self-care tips, or check potential symptoms with our clinical assistant.
        </p>
        <Link 
          to="/chat" 
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-white text-blue-600 font-bold hover:bg-blue-50 transition-colors shadow-sm"
        >
          Start Conversation
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
};

const About = () => {
  const principles = [
    {
      title: "Deterministic Safety Guardrails",
      desc: "Emergency red-flags (such as severe respiratory distress or cyanosis) are caught immediately by rule-based pre-filters in under 15ms, triggering urgent clinical care guidance rather than waiting for generative reasoning.",
      icon: <ShieldAlert className="w-5 h-5 text-red-600" />,
      bg: "bg-red-50"
    },
    {
      title: "Dual Hybrid Retrieval Engine",
      desc: "Combines sparse lexical search (BM25) for precision matching of clinical terminology with dense vector search (FAISS embeddings) for semantic understanding, fused through Reciprocal Rank Fusion (RRF).",
      icon: <Database className="w-5 h-5 text-indigo-600" />,
      bg: "bg-indigo-50"
    },
    {
      title: "Active Ambiguity Resolution",
      desc: "Recognizes vague user queries (e.g., 'I have a cough') and proactively clarifies symptoms, duration, and triggers instead of guessing or giving potentially misleading diagnostic assumptions.",
      icon: <HelpCircle className="w-5 h-5 text-blue-600" />,
      bg: "bg-blue-50"
    },
    {
      title: "Strict Medical Non-Prescription Ethics",
      desc: "Designed to educate and inform, not prescribe. The system strictly refuses dosage modifications, brand prescriptions, and diagnostic declarations, directing patients to certified pulmonologists.",
      icon: <ShieldCheck className="w-5 h-5 text-emerald-600" />,
      bg: "bg-emerald-50"
    }
  ];

  const sources = [
    {
      name: "Global Initiative for Asthma (GINA 2024)",
      desc: "International evidence-based strategy for asthma management, severity staging, and symptom control."
    },
    {
      name: "National Health Service (NHS UK)",
      desc: "Clinical patient protocols, correct inhaler techniques, trigger avoidance, and personalized asthma action plans."
    },
    {
      name: "National Heart, Lung, and Blood Institute (NHLBI)",
      desc: "EPR-3 & EPR-4 clinical guidelines for the diagnosis and comprehensive management of asthma."
    },
    {
      name: "World Health Organization (WHO) & MedlinePlus",
      desc: "Global epidemiological respiratory standards, air quality indices, and patient education material."
    }
  ];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12">
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto mb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold uppercase tracking-wider mb-4">
          <HeartPulse className="w-3.5 h-3.5 text-blue-600" />
          Clinical AI Platform
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight mb-4">
          About RespiraCare AI
        </h1>
        <p className="text-base sm:text-lg text-slate-600 leading-relaxed">
          An evidence-grounded clinical AI assistant engineered to bridge the gap between complex respiratory guidelines and patient accessibility with uncompromising safety.
        </p>
      </div>

      {/* Purpose & Mission Section */}
      <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-slate-200 mb-10">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-blue-50 rounded-xl text-blue-600">
            <Stethoscope className="w-5 h-5" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">Clinical Focus & Purpose</h2>
        </div>
        <p className="text-slate-600 leading-relaxed text-sm sm:text-base mb-4">
          Asthma is a heterogeneous chronic airway disease affecting over 260 million individuals worldwide. While standardized clinical management frameworks like GINA exist, patients often struggle with confusing terminology, poor inhaler adherence, unrecognized environmental triggers, and dangerous misinformation online.
        </p>
        <p className="text-slate-600 leading-relaxed text-sm sm:text-base">
          Standard general-purpose AI chat assistants can produce convincing hallucinations, recommend arbitrary medication dosages, or fail to prioritize urgent medical emergencies. <strong className="text-slate-900 font-semibold">RespiraCare AI</strong> was specifically built to eliminate these risks by pairing constrained generative models with verified knowledge bases and deterministic clinical safety guardrails.
        </p>
      </div>

      {/* Core Architectural Pillars */}
      <div className="mb-12">
        <h2 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-blue-600" />
          Core System Pillars
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {principles.map((item, idx) => (
            <div key={idx} className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-3 mb-3">
                  <div className={`p-2.5 rounded-xl ${item.bg}`}>
                    {item.icon}
                  </div>
                  <h3 className="text-base font-bold text-slate-800">{item.title}</h3>
                </div>
                <p className="text-slate-600 text-sm leading-relaxed">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Authoritative Knowledge Sources */}
      <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-slate-200 mb-10">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-indigo-50 rounded-xl text-indigo-600">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Curated Clinical Knowledge Base</h2>
            <p className="text-xs sm:text-sm text-slate-500">Every response is strictly grounded in peer-reviewed global health standards.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {sources.map((src, i) => (
            <div key={i} className="p-4 rounded-xl bg-slate-50 border border-slate-100">
              <div className="flex items-center gap-2 font-bold text-slate-800 text-sm mb-1">
                <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                {src.name}
              </div>
              <p className="text-xs text-slate-600 leading-relaxed pl-6">{src.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Medical Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 flex gap-4 items-start shadow-sm">
        <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" />
        <div>
          <h3 className="text-sm font-bold text-amber-900 uppercase tracking-wider mb-1">Clinical & Medical Disclaimer</h3>
          <p className="text-sm text-amber-800 leading-relaxed">
            RespiraCare AI is an assistive educational and informational system; it is <strong>not</strong> a medical device and does <strong>not</strong> provide medical diagnoses, treatment plans, or prescription adjustments. Always consult a qualified physician or pulmonologist for clinical decisions. In acute emergencies (severe shortness of breath, inability to speak, cyanosis), contact your local emergency medical services immediately.
          </p>
        </div>
      </div>
    </div>
  );
};

const Navbar = () => {
  const location = useLocation();
  const navItems = [
    { name: 'Home', path: '/' },
    { name: 'Chat', path: '/chat' },
    { name: 'How It Works', path: '/how-it-works' },
    { name: 'About', path: '/about' }
  ];

  return (
    <nav className="bg-white shadow-sm border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="text-xl font-bold text-blue-600 tracking-tight hover:text-blue-700 transition-colors">
              RespiraCare AI
            </Link>
          </div>
          <div className="flex items-center space-x-2 sm:space-x-4">
            {navItems.map(item => (
              <Link 
                key={item.name} 
                to={item.path} 
                className={`px-3 py-2 rounded-xl text-sm font-semibold transition-colors ${
                  location.pathname === item.path 
                    ? 'bg-blue-50 text-blue-600' 
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                {item.name}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
};

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-slate-50 font-sans text-slate-900 flex flex-col">
        <Navbar />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/how-it-works" element={<HowItWorks />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
