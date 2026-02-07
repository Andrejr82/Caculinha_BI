import Icon from '../Icon';
const iconNode = [
    ['circle', { cx: '12', cy: '12', r: '10', key: '1mglay' }],
    ['polygon', { points: '10 8 16 12 10 16 10 8', key: '1cimsy' }],
];
const PlayCircle = (props) => (<Icon {...props} name="PlayCircle" iconNode={iconNode}/>);
export default PlayCircle;
