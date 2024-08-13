import React, { useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  ColumnDef,
  SortingState,
  flexRender,
} from '@tanstack/react-table';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSortUp, faSortDown, faSort} from '@fortawesome/free-solid-svg-icons';

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
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'totalScore', desc: true } // 默认按总分降序排列
  ]);

  const toggleSorting = (columnId: string) => {
    setSorting((prevSorting) => {
      const currentSort = prevSorting.find((sort) => sort.id === columnId);
      if (!currentSort) {
        return [{ id: columnId, desc: true }]; // 如果未排序，则升序排列
      } else if (!currentSort.desc) {
        return [{ id: columnId, desc: true }]; // 如果当前为升序，改为降序
      } else {
        return [{ id: columnId, desc: false }]; // 如果当前为降序，改为升序
      }
    });
  };

  const columns: ColumnDef<LeaderboardEntry>[] = [
    {
      header: '排名',
      accessorFn: (_, i) => i + 1,
      id: 'rank',
      enableSorting: false,
      cell: info => info.getValue(),
    },
    {
      header: '用户名',
      accessorKey: 'username',
      enableSorting: false,
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
    state: {
      sorting,
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
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
                  onClick={() => toggleSorting(header.id as string)}
                  className="px-6 py-3 text-center text-xs font-bold text-white uppercase tracking-wider cursor-pointer select-none"
                >
                  <div className="flex items-center justify-center">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {/* {header.column.getIsSorted() ? (
                      header.column.getIsSorted() === 'asc' ? (
                        <FontAwesomeIcon icon={faSortUp} className="ml-2" />
                      ) : (
                        <FontAwesomeIcon icon={faSortDown} className="ml-2" />
                      )
                    ) : null} */}
                    {header.column.getIsSorted() ? (
                      <FontAwesomeIcon icon={faSort} className="ml-2" />
                    ) : null}
                  </div>
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
