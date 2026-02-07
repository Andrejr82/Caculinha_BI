import { JSX } from 'solid-js';
import { IconNode, LucideProps } from './types';
/**
 * Converts string to KebabCase
 * Copied from scripts/helper. If anyone knows how to properly import it here
 * then please fix it.
 *
 * @param {string} string
 * @returns {string} A kebabized string
 */
export declare const toKebabCase: (string: string) => string;
interface IconProps {
    name: string;
    iconNode: IconNode;
}
declare const Icon: (props: LucideProps & IconProps) => JSX.Element;
export default Icon;
