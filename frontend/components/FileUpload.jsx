"use client";
import { Button } from '@mui/material';

export default function FileUpload({ onSelect }) {
  return (
    <div>
      <input 
        type='file' 
        accept='.txt,.csv'
        onChange={(e)=>onSelect(e.target.files[0])}
      />
    </div>
  );
}
