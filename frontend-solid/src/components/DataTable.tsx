// frontend-solid/src/components/DataTable.tsx

import { createSignal, For, Show, Accessor } from 'solid-js';

interface DataTableProps {
  data: Accessor<any[]>;
  caption?: string;
  itemsPerPage?: number;
}

export const DataTable = (props: DataTableProps) => {
  const [currentPage, setCurrentPage] = createSignal(1);
  const itemsPerPage = props.itemsPerPage || 10;

  const tableData = () => props.data();
  const headers = () => {
    if (tableData().length === 0) return [];
    return Object.keys(tableData()[0]);
  };

  const paginatedData = () => {
    const start = (currentPage() - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    return tableData().slice(start, end);
  };

  const totalPages = () => Math.ceil(tableData().length / itemsPerPage);

  const goToPage = (page: number) => {
    if (page > 0 && page <= totalPages()) {
      setCurrentPage(page);
    }
  };

  const canGoPrev = () => currentPage() > 1;
  const canGoNext = () => currentPage() < totalPages();

  return (
    <div class="overflow-x-auto rounded-lg border shadow-sm my-4">
      <Show when={props.caption}>
        <div class="p-4 text-lg font-semibold text-card-foreground">{props.caption}</div>
      </Show>
      <table class="w-full text-sm text-left text-gray-500">
        <thead class="text-xs text-gray-700 uppercase bg-gray-50">
          <tr>
            <For each={headers()}>
              {(header) => (
                <th scope="col" class="px-6 py-3">
                  {header}
                </th>
              )}
            </For>
          </tr>
        </thead>
        <tbody>
          <Show when={tableData().length > 0} fallback={
            <tr>
                <td colSpan={headers().length} class="px-6 py-4 text-center text-gray-400">Nenhum dado disponível.</td>
            </tr>
          }>
            <For each={paginatedData()}>
              {(row) => (
                <tr class="bg-white border-b hover:bg-gray-50">
                  <For each={headers()}>
                    {(header) => (
                      <td class="px-6 py-4">
                        {typeof row[header] === 'object' && row[header] !== null
                          ? JSON.stringify(row[header])
                          : String(row[header])}
                      </td>
                    )}
                  </For>
                </tr>
              )}
            </For>
          </Show>
        </tbody>
      </table>

      <Show when={totalPages() > 1}>
        <nav class="flex items-center justify-between p-4 border-t bg-gray-50" aria-label="Table navigation">
          <span class="text-sm font-normal text-gray-500">
            Página <span class="font-semibold text-gray-900">{currentPage()}</span> de <span class="font-semibold text-gray-900">{totalPages()}</span>
          </span>
          <ul class="inline-flex -space-x-px text-sm h-8">
            <li>
              <button
                onClick={() => goToPage(currentPage() - 1)}
                disabled={!canGoPrev()}
                class="flex items-center justify-center px-3 h-8 ml-0 leading-tight text-gray-500 bg-white border border-gray-300 rounded-l-lg hover:bg-gray-100 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Anterior
              </button>
            </li>
            <For each={Array(totalPages()).fill(0)}>
              {(_, i) => (
                <li>
                  <button
                    onClick={() => goToPage(i() + 1)}
                    class={`flex items-center justify-center px-3 h-8 leading-tight ${
                      currentPage() === i() + 1
                        ? 'text-primary-foreground bg-primary border-primary hover:bg-primary-dark hover:text-primary-foreground'
                        : 'text-gray-500 bg-white border border-gray-300 hover:bg-gray-100 hover:text-gray-700'
                    }`}
                  >
                    {i() + 1}
                  </button>
                </li>
              )}
            </For>
            <li>
              <button
                onClick={() => goToPage(currentPage() + 1)}
                disabled={!canGoNext()}
                class="flex items-center justify-center px-3 h-8 leading-tight text-gray-500 bg-white border border-gray-300 rounded-r-lg hover:bg-gray-100 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Próxima
              </button>
            </li>
          </ul>
        </nav>
      </Show>
    </div>
  );
};
