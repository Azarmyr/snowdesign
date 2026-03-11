# Architecture Quality Gate

Run through this checklist before delivering any React component output.

### Structural integrity
- [ ] Logic extracted to custom hooks in `src/hooks/`.
- [ ] No monolithic files; Atomic/Composite modularity enforced.
- [ ] All static text/URLs moved to `src/data/mockData.ts`.
- [ ] Components are independently testable and importable.

### Type safety and syntax
- [ ] Props use `Readonly<T>` interfaces named `[ComponentName]Props`.
- [ ] File is syntactically valid TypeScript (no red squiggles).
- [ ] Placeholders from template (e.g., `StitchComponent`) replaced with actual names.
- [ ] No `any` types - use proper interfaces.

### Styling and theming
- [ ] Dark mode (`dark:`) applied to all color classes.
- [ ] No hardcoded hex values - use theme-mapped Tailwind classes.
- [ ] Design tokens from style-guide.json mapped to Tailwind config.
- [ ] `cursor-pointer` on all interactive elements.
- [ ] Hover states with smooth transitions (150-300ms).
- [ ] Focus states visible for keyboard navigation.

### Accessibility
- [ ] Semantic HTML elements used (nav, main, section, article).
- [ ] Text contrast meets 4.5:1 minimum.
- [ ] `prefers-reduced-motion` respected.
- [ ] ARIA labels on interactive elements without visible text.

### Performance
- [ ] No barrel file re-exports that break tree-shaking.
- [ ] Images use lazy loading where appropriate.
- [ ] Heavy components wrapped in React.lazy() if needed.

### Responsive
- [ ] Works at 375px, 768px, 1024px, 1440px breakpoints.
- [ ] No horizontal scroll on mobile.
- [ ] Touch targets minimum 44x44px on mobile.
