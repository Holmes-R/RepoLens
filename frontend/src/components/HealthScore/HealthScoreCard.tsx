interface HealthScoreCardProps {
  score: number;
}

export function HealthScoreCard({ score }: HealthScoreCardProps) {
  const getColor = () => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-amber-600';
    return 'text-red-600';
  };

  const getBgColor = () => {
    if (score >= 80) return 'bg-green-50 border-green-200';
    if (score >= 60) return 'bg-amber-50 border-amber-200';
    return 'bg-red-50 border-red-200';
  };

  const getLabel = () => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
    return 'Needs Work';
  };

  return (
    <div className={`card text-center border-2 ${getBgColor()}`}>
      <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Health Score</div>
      <div className={`text-4xl font-bold ${getColor()}`}>{Math.round(score)}</div>
      <div className="text-xs text-slate-500 mt-1">{getLabel()}</div>
      <div className="w-full bg-slate-200 rounded-full h-2 mt-3">
        <div className={`h-2 rounded-full transition-all duration-500 ${score >= 80 ? 'bg-green-500' : score >= 60 ? 'bg-amber-500' : 'bg-red-500'}`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}
