import React from 'react';
import {
  useReactTable,
  getCoreRowModel,
  ColumnDef,
  flexRender,
} from '@tanstack/react-table';

interface LeaderboardEntry {
  username: string;
  totalScore: number;
  scores: Record<string, number>;
}

interface LeaderboardTableProps {
  leaderboard: LeaderboardEntry[];
  problems: string[];
}

const LeaderboardTable: React.FC<LeaderboardTableProps> = ({ leaderboard, problems }) => {
  const formatTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const columns: ColumnDef<LeaderboardEntry>[] = [
    {
      header: '排名',
      accessorFn: (_, i) => i + 1,
      id: 'rank',
      cell: info => info.getValue(),
    },
    {
      header: '用户名',
      accessorKey: 'username',
      cell: info => info.getValue(),
    },
    {
      header: '总分',
      accessorKey: 'totalScore',
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      cell: (info: any) => (
        <>
          <div>{parseFloat(info.getValue().toFixed(3))}</div>
          <div className="text-xs text-gray-600">{formatTime(info.row.original.totalSubmissionTime)}</div>
        </>
      ),
    },
    ...problems.map(problem => ({
      header: problem,
      accessorFn: (row: LeaderboardEntry) => row.scores[problem] || 0,
      id: problem,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      cell: (info: any) => {
        const score = info.getValue();
        const submissionTime = info.row.original.submissionTimes[problem];
        return (
          <>
            <div>{parseFloat(info.getValue().toFixed(3))}</div>
            <div className="text-xs text-gray-600">
              {score > 0 ? formatTime(submissionTime) : '-'}
            </div>
          </>
        );
      },
    })),
  ];

  const table = useReactTable({
    data: leaderboard,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div 
      className="bg-white bg-opacity-70 shadow-lg rounded-lg w-full max-w-4xl overflow-x-auto"
      style={{
        transform: 'perspective(1000px)',
        transition: 'transform 0.1s ease-out',
        willChange: 'transform',
        WebkitFontSmoothing: 'antialiased',
        WebkitBackfaceVisibility: 'hidden',
      }}
    >
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gradient-to-r from-indigo-500 to-blue-600">
          {table.getHeaderGroups().map(headerGroup => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map(header => (
                <th
                  key={header.id}
                  className="px-6 py-3 text-center text-xs font-bold text-white uppercase tracking-wider select-none"
                >
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {table.getRowModel().rows.map((row, index) => (
            <tr
              key={row.id}
              className={`${index % 2 === 0 ? 'bg-white' : 'bg-gray-100'} hover:bg-gray-200`}
            >
              {row.getVisibleCells().map(cell => (
                <td
                  key={cell.id}
                  className="px-6 py-4 whitespace-nowrap text-sm text-center text-gray-800"
                >
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default LeaderboardTable;
