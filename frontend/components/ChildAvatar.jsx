export default function ChildAvatar({ traits }) {
  const eye = traits.eye_color?.result || "unknown";

  const eyeColorMap = {
    blue: "#74b9ff",
    brown: "#5d4037",
    green: "#81c784",
    hazel: "#8d6e63",
    unknown: "#b0bec5"
  };

  const borderColor = eyeColorMap[eye.toLowerCase()] || "#b0bec5";

  return (
    <div style={{ marginBottom:20, textAlign:'center' }}>
      <div style={{
        width:120, height:120,
        borderRadius:'50%',
        background:'linear-gradient(135deg,#eef2ff,#e0f7ff)',
        display:'flex',
        justifyContent:'center',
        alignItems:'center',
        margin:'auto',
        border:`5px solid ${borderColor}`,
        color:'#0f172a',
        fontWeight:700,
        letterSpacing:0.3
      }}>
        Child
      </div>
      <p>Generated from predicted traits</p>
    </div>
  );
}
