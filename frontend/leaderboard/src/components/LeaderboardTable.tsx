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
      cell: info => info.getValue(),
    },
    ...problems.map(problem => ({
      header: problem,
      accessorFn: (row: LeaderboardEntry) => row.scores[problem] || 0,
      id: problem,
      cell: info => info.getValue(),
    })),
  ];

  const table = useReactTable({
    data: leaderboard,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="bg-white shadow-md rounded-lg w-full max-w-4xl overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gradient-to-r from-indigo-500 to-blue-600">
          {table.getHeaderGroups().map(headerGroup => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map(header => (
                <th
                  key={header.id}
                  className="px-6 py-3 text-center text-xs font-bold text-white uppercase tracking-wider"
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
              className={`${index % 2 === 0 ? 'bg-gray-50' : 'bg-white'} hover:bg-gray-100`}
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
