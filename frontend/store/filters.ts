import { create } from "zustand";
import { subDays } from "date-fns";

interface DateRange {
  from: Date;
  to: Date;
}

interface FiltersStore {
  dateRange: DateRange;
  companyIds: string[];
  bankAccountIds: string[];
  setDateRange: (range: DateRange) => void;
  setCompanyIds: (ids: string[]) => void;
  setBankAccountIds: (ids: string[]) => void;
  reset: () => void;
}

const DEFAULT_DATE_RANGE: DateRange = {
  from: subDays(new Date(), 30),
  to: new Date(),
};

export const useFiltersStore = create<FiltersStore>((set) => ({
  dateRange: DEFAULT_DATE_RANGE,
  companyIds: [],
  bankAccountIds: [],
  setDateRange: (range) => set({ dateRange: range }),
  setCompanyIds: (ids) => set({ companyIds: ids }),
  setBankAccountIds: (ids) => set({ bankAccountIds: ids }),
  reset: () =>
    set({
      dateRange: DEFAULT_DATE_RANGE,
      companyIds: [],
      bankAccountIds: [],
    }),
}));
