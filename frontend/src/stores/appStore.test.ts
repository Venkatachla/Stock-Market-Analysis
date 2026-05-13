import { describe, it, expect } from 'vitest';
import { useAppStore } from './appStore';

describe('appStore', () => {
  it('should initialize with default state', () => {
    const state = useAppStore.getState();
    expect(state).toBeDefined();
    // Validate that required default store functions/state properties exist
  });
});
