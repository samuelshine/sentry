//
// Styled components used by both ListBox and GridList
//

import styled from '@emotion/styled';

import {Button} from 'sentry/components/button';
import space from 'sentry/styles/space';

export const ListWrap = styled('ul')`
  margin: 0;
  padding: ${space(0.5)} 0;

  /* Add 1px to top padding if preceded by menu header, to account for the header's
  shadow border */
  div[data-header] ~ &:first-of-type,
  div[data-header] ~ div > &:first-of-type {
    padding-top: calc(${space(0.5)} + 1px);
  }

  /* Remove top padding if preceded by search input, since search input already has
  vertical padding */
  input ~ &&:first-of-type,
  input ~ div > &&:first-of-type {
    padding-top: 0;
  }

  /* Should scroll if it's in a non-composite select */
  :only-of-type {
    min-height: 0;
    overflow: auto;
  }

  :focus-visible {
    outline: none;
  }
`;

export const ListLabel = styled('p')`
  display: inline-block;
  font-weight: 600;
  font-size: ${p => p.theme.fontSizeExtraSmall};
  color: ${p => p.theme.subText};
  text-transform: uppercase;
  white-space: nowrap;
  margin: ${space(0.5)} ${space(1.5)};
  padding-right: ${space(1)};
`;

export const ListSeparator = styled('div')`
  border-top: solid 1px ${p => p.theme.innerBorder};
  margin: ${space(0.5)} ${space(1.5)};

  :first-child {
    display: none;
  }

  ul:empty + & {
    display: none;
  }
`;

export const SectionWrap = styled('li')`
  list-style-type: none;
`;

export const SectionHeader = styled('div')`
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-sizing: content-box;
  height: 1.5em;
  padding: ${space(0.25)} ${space(1.5)};
`;

export const SectionTitle = styled('p')`
  display: inline-block;
  font-weight: 600;
  font-size: ${p => p.theme.fontSizeExtraSmall};
  color: ${p => p.theme.subText};
  text-transform: uppercase;
  white-space: nowrap;

  margin: 0;
  padding-right: ${space(4)};
`;

export const SectionToggleButton = styled(Button)<{visible: boolean}>`
  padding: 0 ${space(0.5)};
  margin: 0 -${space(0.5)} 0 ${space(2)};
  font-weight: 400;
  font-size: ${p => p.theme.fontSizeSmall};
  color: ${p => p.theme.subText};
  transition: opacity 0.1s;

  &.focus-visible {
    opacity: 1;
    pointer-events: all;
  }

  ${p =>
    p.visible
      ? `
    opacity: 1;
    pointer-events: all;
  `
      : `
    opacity: 0;
    pointer-events: none;
  `}
`;

export const SectionSeparator = styled('li')`
  list-style-type: none;
  border-top: solid 1px ${p => p.theme.innerBorder};
  margin: ${space(0.5)} ${space(1.5)};

  &:first-of-type {
    display: none;
  }
`;

export const SectionGroup = styled('ul')`
  margin: 0;
  padding: 0;
`;

export const CheckWrap = styled('div')<{isSelected: boolean; multiple: boolean}>`
  display: flex;
  justify-content: center;
  align-items: center;
  width: 1em;
  height: 1.4em;
  padding-bottom: 1px;
  pointer-events: none;
`;
