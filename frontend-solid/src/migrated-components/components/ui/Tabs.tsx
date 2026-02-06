import { createSignal, type JSX, ParentComponent, createContext, useContext } from "solid-js";
import { cn } from "../../utils/cn";

// Context para gerenciar estado das tabs
type TabsContextValue = {
  value: () => string | undefined;
  setValue: (value: string) => void;
};

const TabsContext = createContext<TabsContextValue>();

interface TabsProps extends JSX.HTMLAttributes<HTMLDivElement> {
  defaultValue?: string;
  value?: string;
  onValueChange?: (value: string) => void;
}

/**
 * Tabs component - container
 * Migrated from React to SolidJS (Radix UI removed, native implementation with createSignal)
 */
export const Tabs: ParentComponent<TabsProps> = (props) => {
  const [internalValue, setInternalValue] = createSignal(props.defaultValue || props.value || "");
  
  const value = () => props.value !== undefined ? props.value : internalValue();
  const setValue = (newValue: string) => {
    setInternalValue(newValue);
    props.onValueChange?.(newValue);
  };

  return (
    <TabsContext.Provider value={{ value, setValue }}>
      <div
        data-slot="tabs"
        class={cn("flex flex-col gap-2", props.class)}
        {...props}
      >
        {props.children}
      </div>
    </TabsContext.Provider>
  );
};

/**
 * TabsList component - tabs list container
 */
export const TabsList: ParentComponent<JSX.HTMLAttributes<HTMLDivElement>> = (props) => {
  return (
    <div
      data-slot="tabs-list"
      role="tablist"
      class={cn(
        "bg-muted text-muted-foreground inline-flex h-9 w-fit items-center justify-center rounded-lg p-[3px]",
        props.class
      )}
      {...props}
    >
      {props.children}
    </div>
  );
};

interface TabsTriggerProps extends JSX.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string;
}

/**
 * TabsTrigger component - individual tab button
 */
export function TabsTrigger(props: TabsTriggerProps) {
  const context = useContext(TabsContext);
  if (!context) throw new Error("TabsTrigger must be used within Tabs");

  const isActive = () => context.value() === props.value;

  return (
    <button
      data-slot="tabs-trigger"
      data-state={isActive() ? "active" : "inactive"}
      role="tab"
      aria-selected={isActive()}
      onClick={() => context.setValue(props.value)}
      class={cn(
        "data-[state=active]:bg-background dark:data-[state=active]:text-foreground",
        "focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:outline-ring",
        "dark:data-[state=active]:border-input dark:data-[state=active]:bg-input/30",
        "text-foreground dark:text-muted-foreground",
        "inline-flex h-[calc(100%-1px)] flex-1 items-center justify-center gap-1.5",
        "rounded-md border border-transparent px-2 py-1 text-sm font-medium whitespace-nowrap",
        "transition-[color,box-shadow] focus-visible:ring-[3px] focus-visible:outline-1",
        "disabled:pointer-events-none disabled:opacity-50 data-[state=active]:shadow-sm",
        "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        props.class
      )}
      {...props}
    />
  );
}

interface TabsContentProps extends JSX.HTMLAttributes<HTMLDivElement> {
  value: string;
}

/**
 * TabsContent component - tab panel content
 */
export const TabsContent: ParentComponent<TabsContentProps> = (props) => {
  const context = useContext(TabsContext);
  if (!context) throw new Error("TabsContent must be used within Tabs");

  const isActive = () => context.value() === props.value;

  return (
    <div
      data-slot="tabs-content"
      data-state={isActive() ? "active" : "inactive"}
      role="tabpanel"
      hidden={!isActive()}
      class={cn("flex-1 outline-none", props.class)}
      {...props}
    >
      {isActive() && props.children}
    </div>
  );
};
