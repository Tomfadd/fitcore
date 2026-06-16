export const calcBMI = (weight, height) => (weight / ((height / 100) ** 2)).toFixed(1);

export const calcRFM = (weight, height, gender) => {
  const g = gender === 'female' ? 12 : 0;
  const v = 64 - (20 * (height / 100) / Math.sqrt(weight / height)) + g;
  return Math.max(5, Math.min(60, v)).toFixed(1);
};

export const bmiCategory = (bmi) => {
  if (bmi < 18.5) return { label: 'Underweight', color: '#ffa502' };
  if (bmi < 25)   return { label: 'Normal',      color: '#00ff88' };
  if (bmi < 30)   return { label: 'Overweight',  color: '#ffa502' };
  return               { label: 'Obese',         color: '#ff4757' };
};

export const intensityColor = (level) => ({
  Low:      '#00ff88',
  Moderate: '#00e5ff',
  High:     '#ff6b35',
}[level] || '#6b8599');

export const fmtDate = (d) => new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
