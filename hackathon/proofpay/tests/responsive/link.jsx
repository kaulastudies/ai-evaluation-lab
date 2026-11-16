import React from 'react';
export default function Link({href,children,...props}) {
  return <a {...props} href={href==='/'?window.location.href:href}>{children}</a>;
}
