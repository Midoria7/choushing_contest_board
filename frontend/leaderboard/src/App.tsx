import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { format, parseISO } from 'date-fns';
import zhCN from 'date-fns/locale/zh-CN';
import LeaderboardTable from './components/LeaderboardTable';

interface CompetitionInfo {
  competition_name: string;
  description: string;
  problems: string[];
  start_time: string;
  end_time: string;
}

interface LeaderboardEntry {
  username: string;
  totalScore: number;
  scores: Record<string, number>;
}

const App: React.FC = () => {
  const [competitionInfo, setCompetitionInfo] = useState<CompetitionInfo | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [rotation, setRotation] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const fetchCompetitionInfo = async () => {
      try {
        const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/competition_info`);
        setCompetitionInfo(response.data);
      } catch (error) {
        console.error('Error fetching competition info:', error);
      }
    };

    const fetchLeaderboard = async () => {
      try {
        const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/leaderboard`);
        const data = response.data;

        // 合并同一用户的成绩
        const userScores: Record<string, LeaderboardEntry> = {};

        Object.entries(data).forEach(([problem, entries]: [string, any]) => {
          entries.forEach((entry: any) => {
            const { username, score } = entry;

            if (!userScores[username]) {
              userScores[username] = {
                username,
                totalScore: 0,
                scores: {},
              };
            }

            // 更新该用户的分数
            userScores[username].scores[problem] = score;
            userScores[username].totalScore += score;
          });
        });

        // 将对象转换为数组，并根据总分进行排序
        const leaderboardData = Object.values(userScores).sort((a, b) => b.totalScore - a.totalScore);

        setLeaderboard(leaderboardData);
      } catch (error) {
        console.error('Error fetching leaderboard:', error);
      }
    };

    fetchCompetitionInfo();
    fetchLeaderboard();
  }, []);

  const calculateProgress = () => {
    if (competitionInfo) {
      const startTime = new Date(competitionInfo.start_time).getTime();
      const endTime = new Date(competitionInfo.end_time).getTime();
      const currentTime = new Date().getTime();
      if (currentTime < startTime) {
        return 0;
      }
      const totalDuration = endTime - startTime;
      const elapsed = currentTime - startTime;
      return Math.min((elapsed / totalDuration) * 100, 100);
    }
    return 0;
  };

  const formatDate = (dateString: string) => {
    return format(parseISO(dateString), 'yyyy.MM.dd HH:mm', { locale: zhCN });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left; // 鼠标相对于 div 左上角的水平位置
    const y = e.clientY - rect.top;  // 鼠标相对于 div 左上角的垂直位置

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateX = (centerY - y) / centerY * 0.5;
    const rotateY = (x - centerX) / centerX * 0.5;

    setRotation({ x: rotateX, y: rotateY });
  };

  const handleMouseLeave = () => {
    setRotation({ x: 0, y: 0 }); // 鼠标离开时重置旋转
  };

  return (
    <div className="bg-custom-gradient-blue-sky min-h-screen flex flex-col items-center p-4">
      {competitionInfo && (
        <div 
          className="bg-white bg-opacity-80 shadow-lg rounded-lg p-6 mt-8 mb-4 w-full max-w-4xl text-center backdrop-filter backdrop-blur-lg backdrop-brightness-125 border border-white border-opacity-25"
          style={{
            transform: `perspective(1000px) rotateX(${rotation.x}deg) rotateY(${rotation.y}deg)`,
            transition: 'transform 0.1s ease-out',
            willChange: 'transform',
            WebkitFontSmoothing: 'antialiased',
            WebkitBackfaceVisibility: 'hidden',
          }}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
        >
          <h1 className="text-4xl font-bold mt-3 mb-3 bg-clip-text bg-gradient-to-r from-indigo-400 to-blue-600 text-transparent">
            {competitionInfo.competition_name} 实时榜单
          </h1>
          <p className="text-lg text-gray-800 break-words mb-4">{competitionInfo.description}</p>
          <div className="w-full bg-gray-300 rounded-full h-4 mb-4 relative">
            <div
              className="bg-gradient-to-r from-green-400 to-blue-500 h-4 rounded-full transition-width duration-500"
              style={{ width: `${calculateProgress()}%` }}
            ></div>
            <div
              className="absolute top-1/2 transform -translate-y-1/2 w-6 h-6 bg-gradient-to-r from-gray-100 to-gray-200 rounded-full shadow-lg border border-gray-300"
              style={{ left: `${Math.max(calculateProgress() - 1, 0)}%`, transform: 'translate(-50%, -50%)' }}
            ></div>
            <div className="flex absolute top-6 w-full text-xs text-gray-600">
              <div className="flex-1 text-left">
                {formatDate(competitionInfo.start_time)}
              </div>
              <div className="flex-1 text-center">
                {(() => {
                  const progress = calculateProgress();
                  if (progress === 100) {
                    return <span>已结束</span>;
                  } else if (progress === 0) {
                    return <span>未开始</span>;
                  } else {
                    return <span>进行中</span>;
                  }
                })()}
              </div>
              <div className="flex-1 text-right">
                {formatDate(competitionInfo.end_time)}
              </div>
            </div>
          </div>
        </div>
      )}
      <LeaderboardTable leaderboard={leaderboard} problems={competitionInfo?.problems || []} />
    </div>
  );
};

export default App;
