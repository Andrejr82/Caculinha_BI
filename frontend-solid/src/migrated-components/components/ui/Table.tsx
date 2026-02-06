import type { JSX, ParentComponent } from "solid-js";
import { cn } from "../../utils/cn";

interface TableProps extends JSX.HTMLAttributes<HTMLTableElement> {}

/**
 * Table component - table container with scroll
 * Migrated from React to SolidJS
 */
export const Table: ParentComponent<TableProps> = (props) => {
  return (
    <div
      data-slot="table-container"
      class="relative w-full overflow-x-auto"
    >
      <table
        data-slot="table"
        class={cn("w-full caption-bottom text-sm", props.class)}
        {...props}
      >
        {props.children}
      </table>
    </div>
  );
};

/**
 * TableHeader component - thead element
 */
export const TableHeader: ParentComponent<JSX.HTMLAttributes<HTMLTableSectionElement>> = (props) => {
  return (
    <thead
      data-slot="table-header"
      class={cn("[&_tr]:border-b", props.class)}
      {...props}
    >
      {props.children}
    </thead>
  );
};

/**
 * TableBody component - tbody element
 */
export const TableBody: ParentComponent<JSX.HTMLAttributes<HTMLTableSectionElement>> = (props) => {
  return (
    <tbody
      data-slot="table-body"
      class={cn("[&_tr:last-child]:border-0", props.class)}
      {...props}
    >
      {props.children}
    </tbody>
  );
};

/**
 * TableFooter component - tfoot element
 */
export const TableFooter: ParentComponent<JSX.HTMLAttributes<HTMLTableSectionElement>> = (props) => {
  return (
    <tfoot
      data-slot="table-footer"
      class={cn(
        "bg-muted/50 border-t font-medium [&>tr]:last:border-b-0",
        props.class
      )}
      {...props}
    >
      {props.children}
    </tfoot>
  );
};

/**
 * TableRow component - tr element
 */
export const TableRow: ParentComponent<JSX.HTMLAttributes<HTMLTableRowElement>> = (props) => {
  return (
    <tr
      data-slot="table-row"
      class={cn(
        "hover:bg-muted/50 data-[state=selected]:bg-muted border-b transition-colors",
        props.class
      )}
      {...props}
    >
      {props.children}
    </tr>
  );
};

/**
 * TableHead component - th element
 */
export const TableHead: ParentComponent<JSX.ThHTMLAttributes<HTMLTableCellElement>> = (props) => {
  return (
    <th
      data-slot="table-head"
      class={cn(
        "text-foreground h-10 px-2 text-left align-middle font-medium whitespace-nowrap",
        "[&:has([role=checkbox])]:pr-0 [&>[role=checkbox]]:translate-y-[2px]",
        props.class
      )}
      {...props}
    >
      {props.children}
    </th>
  );
};

/**
 * TableCell component - td element
 */
export const TableCell: ParentComponent<JSX.TdHTMLAttributes<HTMLTableCellElement>> = (props) => {
  return (
    <td
      data-slot="table-cell"
      class={cn(
        "p-2 align-middle whitespace-nowrap",
        "[&:has([role=checkbox])]:pr-0 [&>[role=checkbox]]:translate-y-[2px]",
        props.class
      )}
      {...props}
    >
      {props.children}
    </td>
  );
};

/**
 * TableCaption component - caption element
 */
export const TableCaption: ParentComponent<JSX.HTMLAttributes<HTMLTableCaptionElement>> = (props) => {
  return (
    <caption
      data-slot="table-caption"
      class={cn("text-muted-foreground mt-4 text-sm", props.class)}
      {...props}
    >
      {props.children}
    </caption>
  );
};
