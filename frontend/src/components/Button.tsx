import type { ButtonHTMLAttributes } from 'react'
import { buttonClass, type ButtonVariant } from '../lib/styles'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }

export function Button({ variant = 'primary', className = '', type = 'button', ...rest }: Props) {
  return <button type={type} className={buttonClass(variant, className)} {...rest} />
}
