// downloadReport.js
// Uses jsPDF to generate a PDF report from dashboard/profile data
import jsPDF from 'jspdf';

export async function downloadUserReport() {
  // Fetch user profile and logs (adjust endpoints as needed)
  const [profileRes, workoutRes, nutritionRes] = await Promise.all([
    fetch('/api/profile'),
    fetch('/api/workout_timeseries'),
    fetch('/api/nutrition_timeseries'),
  ]);
  const profile = await profileRes.json();
  const workout = await workoutRes.json();
  const nutrition = await nutritionRes.json();

  const doc = new jsPDF();
  let y = 20;
  doc.setFontSize(22);
  doc.setTextColor(239, 68, 68); // FitFusion red
  doc.text('FitFusion User Report', 15, y);
  y += 10;
  doc.setFontSize(14);
  doc.setTextColor(33, 37, 41);
  doc.text(`Name: ${profile.name || ''}`, 15, y += 10);
  doc.text(`Email: ${profile.email || ''}`, 15, y += 10);
  doc.text(`Age: ${profile.age || ''}`, 15, y += 10);
  doc.text(`Gender: ${profile.gender || ''}`, 15, y += 10);
  doc.text(`Height: ${profile.height || ''} cm`, 15, y += 10);
  doc.text(`Weight: ${profile.weight || ''} kg`, 15, y += 10);
  doc.text(`Fitness Goal: ${profile.fitness_goal || ''}`, 15, y += 10);

  // Workout summary
  doc.setFontSize(16);
  doc.setTextColor(185, 28, 28);
  doc.text('Workout Logs (last 7 days)', 15, y += 15);
  doc.setFontSize(12);
  doc.setTextColor(33, 37, 41);
  if (workout.labels && workout.data) {
    workout.labels.forEach((date, i) => {
      doc.text(`${date}: ${workout.data[i]} workouts`, 15, y += 8);
    });
  }
  // Nutrition summary
  doc.setFontSize(16);
  doc.setTextColor(185, 28, 28);
  doc.text('Nutrition Logs (last 7 days)', 15, y += 15);
  doc.setFontSize(12);
  doc.setTextColor(33, 37, 41);
  if (nutrition.labels && nutrition.data) {
    nutrition.labels.forEach((date, i) => {
      doc.text(`${date}: ${nutrition.data[i]} calories`, 15, y += 8);
    });
  }
  doc.save('FitFusion_User_Report.pdf');
}
