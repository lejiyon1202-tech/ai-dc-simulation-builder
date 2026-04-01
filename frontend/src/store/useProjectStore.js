import { create } from 'zustand';

const useProjectStore = create((set, get) => ({
  // 현재 프로젝트 상태
  currentProject: {
    id: null,
    name: '',
    description: '',
    evaluationPurpose: '',
    targetLevel: '',
    industry: '',
    jobFunction: '',
    competencies: [],
    simulations: []
  },

  // 선택 단계 상태
  currentStep: 1,
  totalSteps: 8,
  selections: {},

  // 로딩 상태
  loading: false,
  error: null,

  // 액션
  setCurrentStep: (step) => set({ currentStep: step }),

  updateSelection: (step, data) => 
    set((state) => ({
      selections: {
        ...state.selections,
        [step]: data
      }
    })),

  setCurrentProject: (project) => set({ currentProject: project }),

  updateCurrentProject: (updates) => 
    set((state) => ({
      currentProject: {
        ...state.currentProject,
        ...updates
      }
    })),

  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),

  reset: () => set({
    currentProject: {
      id: null,
      name: '',
      description: '',
      evaluationPurpose: '',
      targetLevel: '',
      industry: '',
      jobFunction: '',
      competencies: [],
      simulations: []
    },
    currentStep: 1,
    selections: {},
    loading: false,
    error: null
  }),

  // 선택 완료 여부 체크
  isStepCompleted: (step) => {
    const state = get();
    return !!state.selections[step];
  },

  // 다음 단계로 진행 가능 여부
  canProceed: () => {
    const state = get();
    return state.isStepCompleted(state.currentStep);
  },

  // 진행률 계산
  getProgress: () => {
    const state = get();
    return (state.currentStep / state.totalSteps) * 100;
  }
}));

export default useProjectStore;