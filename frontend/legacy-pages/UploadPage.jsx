
import React,{useState,useEffect} from "react";
import { LinearProgress, Box, Button, Card, CardContent, Typography } from "@mui/material";

export default function UploadPage(){
 const [file,setFile] = useState(null);
 const [uploading,setUploading] = useState(false);
 const [processing,setProcessing] = useState(false);
 const [progress,setProgress] = useState(0);

 useEffect(()=>{
   if(!processing) return;
   const t=setInterval(async()=>{
     const r=await fetch("http://localhost:5000/progress");
     const d=await r.json();
     setProgress(d.progress);
   },300);
   return()=>clearInterval(t);
 },[processing]);

 async function upload(){
   if(!file) return alert("Select a file");
   setUploading(true);

   const form=new FormData();
   form.append("file",file);

   const res=await fetch("http://localhost:5000/upload",{method:"POST",body:form});
   const data=await res.json();
   setUploading(false);
   setProcessing(false);

   if(!res.ok) return alert(data.error);
   localStorage.setItem("report",JSON.stringify(data));
   window.location="/report";
 }

 return(
   <Card sx={{maxWidth:600,margin:"40px auto",padding:3}}>
     <CardContent>
       <Typography variant="h4">DNA Insight</Typography>
       <input type="file" onChange={e=>setFile(e.target.files[0])}/>
       <Button variant="contained" onClick={upload} sx={{mt:2}}>Analyze</Button>
       {uploading && <Box><p>Uploading…</p><LinearProgress/></Box>}
       {processing && <Box><p>Processing…</p><LinearProgress variant="determinate" value={progress}/></Box>}
     </CardContent>
   </Card>
 );
}
