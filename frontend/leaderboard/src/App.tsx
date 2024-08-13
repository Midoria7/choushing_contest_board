import React, { useEffect, useState } from 'react';
import axios from 'axios';
import LeaderboardTable from './components/LeaderboardTable';

interface CompetitionInfo {
  competition_name: string;
  description: string;
  problems: string[];
}

interface LeaderboardEntry {
  username: string;
  totalScore: number;
  scores: Record<string, number>;
}

const App: React.FC = () => {
  const [competitionInfo, setCompetitionInfo] = useState<CompetitionInfo | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);

  useEffect(() => {
    const fetchCompetitionInfo = async () => {
      try {
        const response = await axios.get('http://localhost:5000/competition_info');
        setCompetitionInfo(response.data);
      } catch (error) {
        console.error('Error fetching competition info:', error);
      }
    };

    const fetchLeaderboard = async () => {
      try {
        const response = await axios.get('http://localhost:5000/leaderboard');
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

  return (
    <div className="container mx-auto p-4">
      {competitionInfo && (
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-5 mt-5">{competitionInfo.competition_name}</h1>
          <p className="text-lg text-gray-700">{competitionInfo.description}</p>
        </div>
      )}
      <LeaderboardTable leaderboard={leaderboard} problems={competitionInfo?.problems || []} />
    </div>
  );
};

export default App;
