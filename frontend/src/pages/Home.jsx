import { Link } from 'react-router-dom';
import { ArrowRight, MessageSquare, ShieldCheck, HelpCircle } from 'lucide-react';

function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 relative overflow-hidden">
      {/* Decorative background blobs */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-indigo-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{ animationDelay: '2s' }}></div>
      <div className="absolute -bottom-32 left-1/2 w-96 h-96 bg-purple-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{ animationDelay: '4s' }}></div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 relative z-10">
        {/* Hero Section */}
        <div className="text-center max-w-4xl mx-auto mb-20">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 backdrop-blur-md shadow-sm border border-white/50 text-blue-700 font-medium mb-8">
            <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Project Based Learning Capstone (23AI402)
          </div>

          <h1 className="text-5xl md:text-7xl font-extrabold text-slate-900 tracking-tight mb-8 leading-tight">
            RespiraCare <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">AI</span>
          </h1>

          <p className="text-xl md:text-2xl text-slate-600 mb-12 leading-relaxed max-w-3xl mx-auto">
            An asthma information assistant that asks follow-up questions, answers only from trusted sources (WHO, NHS, NHLBI, MedlinePlus) and shows its sources.
          </p>

          <div className="flex justify-center">
            <Link
              to="/chat"
              className="group flex items-center justify-center gap-3 px-8 py-4 bg-blue-600 text-white text-lg font-semibold rounded-2xl shadow-lg hover:shadow-xl hover:bg-blue-700 hover:-translate-y-1 transition-all duration-300"
            >
              Start chat
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          <div className="bg-white/70 backdrop-blur-xl p-8 rounded-3xl shadow-sm border border-white/60 hover:shadow-md transition-all">
            <div className="w-14 h-14 bg-blue-100 rounded-2xl flex items-center justify-center mb-6">
              <HelpCircle className="w-7 h-7 text-blue-600" />
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-3">Asks before it answers</h3>
            <p className="text-slate-600 leading-relaxed">
              Recognizes vague complaints like "I have a cough" and pauses to ask targeted follow-up questions instead of guessing or hallucinating.
            </p>
          </div>

          <div className="bg-white/70 backdrop-blur-xl p-8 rounded-3xl shadow-sm border border-white/60 hover:shadow-md transition-all">
            <div className="w-14 h-14 bg-emerald-100 rounded-2xl flex items-center justify-center mb-6">
              <MessageSquare className="w-7 h-7 text-emerald-600" />
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-3">Grounded answers with citations</h3>
            <p className="text-slate-600 leading-relaxed">
              Every response is generated strictly from curated asthma clinical passages, complete with interactive source chips and verified URLs.
            </p>
          </div>

          <div className="bg-white/70 backdrop-blur-xl p-8 rounded-3xl shadow-sm border border-white/60 hover:shadow-md transition-all">
            <div className="w-14 h-14 bg-red-100 rounded-2xl flex items-center justify-center mb-6">
              <ShieldCheck className="w-7 h-7 text-red-600" />
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-3">Safety first: emergency detection and honest no-answer</h3>
            <p className="text-slate-600 leading-relaxed">
              Flags red-flag emergency symptoms immediately, detects unsafe inputs, and provides an honest "no reliable answer" when sources do not match.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;
