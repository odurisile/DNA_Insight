export default function TraitCard({ title, value }) {
  return (
    <div style={{ padding:10, border:'1px solid #ccc', marginBottom:10 }}>
      <strong>{title}:</strong> {value}
    </div>
  );
}
