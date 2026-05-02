// GAIS — content (calmer, more specific & human)

const CONCEPTS = [
  { id: 'alg-ineq', name: 'Inequalities', section: 'Quant', mastery: 0.54, trend: -0.06, weak: true },
  { id: 'prob-cond', name: 'Conditional Probability', section: 'Quant', mastery: 0.42, trend: -0.11, weak: true },
  { id: 'geom-tri', name: 'Triangles', section: 'Quant', mastery: 0.78, trend: 0.04 },
  { id: 'num-prop', name: 'Number Properties', section: 'Quant', mastery: 0.91, trend: 0.02, strong: true },
  { id: 'data-int', name: 'Data Interpretation', section: 'Quant', mastery: 0.66, trend: 0.08 },
  { id: 'word-prob', name: 'Word Problems', section: 'Quant', mastery: 0.71, trend: 0.05 },
  { id: 'verb-tc', name: 'Text Completion', section: 'Verbal', mastery: 0.83, trend: 0.03, strong: true },
  { id: 'verb-rc', name: 'Reading Comprehension', section: 'Verbal', mastery: 0.69, trend: 0.07 },
  { id: 'verb-se', name: 'Sentence Equivalence', section: 'Verbal', mastery: 0.58, trend: -0.03, weak: true },
  { id: 'verb-vocab', name: 'High-Frequency Vocab', section: 'Verbal', mastery: 0.75, trend: 0.06 },
];

const QUESTIONS = [
  {
    id: 'q-1042', concept: 'prob-cond', section: 'Quant', difficulty: 0.78, type: 'Multiple choice',
    prompt: 'A bag contains 5 red marbles and 3 blue marbles. Two marbles are drawn at random without replacement. Given that the first marble drawn is red, what is the probability that the second marble drawn is also red?',
    choices: [
      { letter: 'A', text: '5/8' }, { letter: 'B', text: '4/7' },
      { letter: 'C', text: '5/14' }, { letter: 'D', text: '1/2' }, { letter: 'E', text: '3/7' },
    ],
    correct: 'B',
    explanation: 'After removing one red marble, four reds remain out of seven total. The conditional probability P(R₂ | R₁) = 4/7.',
  },
  {
    id: 'q-1067', concept: 'verb-se', section: 'Verbal', difficulty: 0.65, type: 'Sentence equivalence',
    prompt: 'Despite the committee\'s ostensibly ___ stance on the matter, internal memos revealed a far more contentious debate had taken place behind closed doors.',
    context: 'Select two answer choices that produce sentences with equivalent meanings.',
    choices: [
      { letter: 'A', text: 'unanimous' }, { letter: 'B', text: 'fractious' },
      { letter: 'C', text: 'concordant' }, { letter: 'D', text: 'preliminary' },
      { letter: 'E', text: 'didactic' }, { letter: 'F', text: 'mercurial' },
    ],
    correct: 'A',
    explanation: 'The contrast cue ("Despite … contentious debate") demands a synonym for "in agreement." Both unanimous and concordant fit.',
  },
  {
    id: 'q-1088', concept: 'alg-ineq', section: 'Quant', difficulty: 0.71, type: 'Quantitative comparison',
    prompt: 'If 3x − 7 ≥ 2x + 5 and y < x − 4, which of the following must be true?',
    choices: [
      { letter: 'A', text: 'y < 8' }, { letter: 'B', text: 'y > 8' },
      { letter: 'C', text: 'y ≥ 12' }, { letter: 'D', text: 'y < 12' }, { letter: 'E', text: 'x = 12' },
    ],
    correct: 'A',
    explanation: 'Solving 3x − 7 ≥ 2x + 5 yields x ≥ 12. Substituting into y < x − 4 forces y < 8.',
  },
];

const ACCURACY_TIMELINE = [
  { d: 'Jan 14', a: 0.51 }, { d: 'Jan 16', a: 0.54 }, { d: 'Jan 18', a: 0.58 },
  { d: 'Jan 20', a: 0.61 }, { d: 'Jan 22', a: 0.60 }, { d: 'Jan 24', a: 0.66 },
  { d: 'Jan 26', a: 0.65 }, { d: 'Jan 28', a: 0.71 }, { d: 'Jan 30', a: 0.69 },
  { d: 'Feb 01', a: 0.73 }, { d: 'Today', a: 0.79 },
];

Object.assign(window, { CONCEPTS, QUESTIONS, ACCURACY_TIMELINE });
