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
    <table className="min-w-full bg-white border border-gray-200">
      <thead>
        {table.getHeaderGroups().map(headerGroup => (
          <tr key={headerGroup.id} className="bg-gray-100">
            {headerGroup.headers.map(header => (
              <th
                key={header.id}
                className="py-2 px-4 border-b border-gray-200 text-left text-sm font-semibold text-gray-600"
              >
                {flexRender(header.column.columnDef.header, header.getContext())}
              </th>
            ))}
          </tr>
        ))}
      </thead>
      <tbody>
        {table.getRowModel().rows.map(row => (
          <tr key={row.id} className="hover:bg-gray-50">
            {row.getVisibleCells().map(cell => (
              <td
                key={cell.id}
                className="py-2 px-4 border-b border-gray-200 text-sm text-gray-700"
              >
                {flexRender(cell.column.columnDef.cell, cell.getContext())}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default LeaderboardTable;
